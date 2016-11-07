
# import builtins
import sys, os, itertools, operator
from collections import OrderedDict
import datetime

# import shapely geometry compatibility functions
# ...and rename them for clarity
import shapely
from shapely.geometry import asShape as geojson2shapely

# import rtree for spatial indexing
import rtree

# import internal modules
from . import loader
from . import saver






class _ModuleFuncsAsClassMethods(object):
    "Helps access this module's functions as vectordata class methods by automatically inserting self as the first arg"
    def __init__(self, data, module):
        from functools import wraps
        self.data = data

        for k,v in module.__dict__.items():
            if hasattr(v, "__call__") and not v.__name__.startswith("_"):
                func = v
                def as_method(func):
                    @wraps(func)
                    def firstarg_inserted(*args, **kwargs):
                        # wrap method to insert self data as the first arg
                        args = [self.data] + list(args)
                        return func(*args, **kwargs)
                    return firstarg_inserted
                self.__dict__[k] = as_method(func)





class Feature:
    def __init__(self, data, row, geometry, id=None):
        "geometry must be a geojson dictionary"
        self._data = data
        self.row  = list(row)

        if geometry:
            geometry = geometry.copy()
            bbox = geometry.get("bbox")
            self._cached_bbox = bbox
        else:
            self._cached_bbox = None

        self.geometry = geometry

        # ensure it is same geometry type as parent
        if self.geometry:
            geotype = geometry["type"]
            if self._data.type: 
                if "Point" in geotype and self._data.type == "Point": pass
                elif "LineString" in geotype and self._data.type == "LineString": pass
                elif "Polygon" in geotype and self._data.type == "Polygon": pass
                else:
                    raise TypeError("Each feature geometry must be of the same type as the file it is attached to")
            else: self._data.type = self.geometry["type"].replace("Multi", "")
        
        if id == None: id = next(self._data._id_generator)
        self.id = id

    def __getitem__(self, i):
        if isinstance(i, (str,unicode)):
            i = self._data.fields.index(i)
        return self.row[i]

    def __setitem__(self, i, setvalue):
        if isinstance(i, (str,unicode)):
            i = self._data.fields.index(i)
        self.row[i] = setvalue

    @property
    def __geo_interface__(self):
        return dict(type="Feature",
                    geometry=self.geometry,
                    properties=dict(zip(self._data.fields,self.row))
                    )

    @property
    def bbox(self):
        if not self.geometry:
            raise Exception("Cannot get bbox of null geometry")
        if not self._cached_bbox:
            geotype = self.geometry["type"]
            coords = self.geometry["coordinates"]

            if geotype == "Point":
                x,y = coords
                bbox = [x,y,x,y]
            elif geotype in ("MultiPoint","LineString"):
                xs, ys = itertools.izip(*coords)
                bbox = [min(xs),min(ys),max(xs),max(ys)]
            elif geotype == "MultiLineString":
                xs = [x for line in coords for x,y in line]
                ys = [y for line in coords for x,y in line]
                bbox = [min(xs),min(ys),max(xs),max(ys)]
            elif geotype == "Polygon":
                exterior = coords[0]
                xs, ys = itertools.izip(*exterior)
                bbox = [min(xs),min(ys),max(xs),max(ys)]
            elif geotype == "MultiPolygon":
                xs = [x for poly in coords for x,y in poly[0]]
                ys = [y for poly in coords for x,y in poly[0]]
                bbox = [min(xs),min(ys),max(xs),max(ys)]
            self._cached_bbox = bbox
        return self._cached_bbox

    def get_shapely(self):
        if not self.geometry:
            raise Exception("Cannot get shapely object of null geometry")
        return geojson2shapely(self.geometry)                

    def copy(self):
        geoj = self.geometry
        if self.geometry and self._cached_bbox: geoj["bbox"] = self._cached_bbox
        return Feature(self._data, self.row, geoj)

    # Easy access to shapely methods

    @property
    def length(self):
        return self.get_shapely().length

    @property
    def area(self):
        return self.get_shapely().area

    @property
    def geodetic_length(self):
        from ._helpers import geodetic_length
        return geodetic_length(self.geometry)

    # convenient visualizing

    def render(self, width, height, bbox=None, flipy=True, **styleoptions):
        from .. import renderer
        singledata = renderer.VectorData()
        singledata.add_feature(self.row, self.geometry)
        lyr = renderer.VectorLayer(singledata, **styleoptions)
        lyr.render(width=width, height=height, bbox=bbox, flipy=flipy)
        return lyr

    def view(self, width, height, bbox=None, flipy=True, **styleoptions):
        lyr = self.render(width, height, bbox, flipy, **styleoptions)
        
        import Tkinter as tk
        import PIL.ImageTk
        
        app = tk.Tk()
        tkimg = PIL.ImageTk.PhotoImage(lyr.img)
        lbl = tk.Label(image=tkimg)
        lbl.tkimg = tkimg
        lbl.pack()
        app.mainloop()




def ID_generator():
    i = 0
    while True:
        yield i
        i += 1



class VectorData:
    def __init__(self, filepath=None, type=None, **kwargs):
        self.filepath = filepath

        # type is optional and will make the features ensure that all geometries are of that type
        # if None, type enforcement will be based on first geometry found
        self.type = type
        
        if filepath:
            fields,rows,geometries,crs = loader.from_file(filepath, **kwargs)
        else:
            fields,rows,geometries,crs = [],[],[],"+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

        self.fields = fields

        self._id_generator = ID_generator()
        
        ids_rows_geoms = itertools.izip(self._id_generator,rows,geometries)
        featureobjs = (Feature(self,row,geom,id=id) for id,row,geom in ids_rows_geoms )
        self.features = OrderedDict([ (feat.id,feat) for feat in featureobjs ])
        self.crs = crs

    def __repr__(self):
        attrs = dict(filepath=self.filepath,
                     type=self.type,
                     length=len(self),
                     )
        if any((f.geometry for f in self)):
            attrs["bbox"] = self.bbox
        else:
            attrs["bbox"] = None
        return "<Vector data: type={type} length={length} bbox={bbox} filepath='{filepath}'>".format(**attrs)

    def __len__(self):
        """
        How many features in data.
        """
        return len(self.features)

    def __iter__(self):
        """
        Loop through features in order.
        """
        for feat in self.features.itervalues():
            yield feat

    def __getitem__(self, i):
        """
        Get a Feature based on its feature id.
        """
        if isinstance(i, slice):
            raise Exception("Can only get one feature at a time")
        else:
            return self.features[i]

    def __setitem__(self, i, feature):
        """
        Set a Feature based on its feature id.
        """
        if isinstance(i, slice):
            raise Exception("Can only set one feature at a time")
        else:
            self.features[i] = feature

    def has_geometry(self):
        return any((feat.geometry for feat in self))

    @property
    def bbox(self):
        if self.has_geometry():
            xmins, ymins, xmaxs, ymaxs = itertools.izip(*(feat.bbox for feat in self if feat.geometry))
            bbox = min(xmins),min(ymins),max(xmaxs),max(ymaxs)
            return bbox
        else:
            raise Exception("Cannot get bbox since there are no features with geometries")

    ### DATA ###

    def add_feature(self, row, geometry=None):
        feature = Feature(self, row, geometry)
        self[feature.id] = feature

    def add_field(self, field, index=None):
        if index is None:
            self.fields.append(field)
            for feat in self:
                feat.row.append(None)
        else:
            self.fields.insert(index, field)
            for feat in self:
                feat.row.insert(index, None)

    def compute(self, field, value, by=None, stat=None):
        if field not in self.fields:
            self.add_field(field)

        if hasattr(value, "__call__"):
            valfunc = value
        else:
            valfunc = lambda f: value

        if by:
            from . import sql
            fieldmapping = [(field, valfunc, stat)]
            for feats in sql.groupby(self, key=by):
                feats = list(feats)
                # aggregate stat for each bygroup
                aggval = sql.aggreg(feats, aggregfuncs=fieldmapping)[0]
                # then write to every group member
                for feat in feats:
                    feat[field] = aggval
        else:
            for feat in self:
                feat[field] = valfunc(feat)

    def drop_field(self, field):
        fieldindex = self.fields.index(field)
        del self.fields[fieldindex]
        for feat in self:
            del feat.row[fieldindex]

    def drop_fields(self, fields):
        for f in fields:
            self.drop_field(f)

    def keep_fields(self, fields):
        for kf in fields:
            if kf not in self.fields:
                raise Exception("%s is not a field")
        for f in reversed(self.fields):
            if f not in fields:
                self.drop_field(f)

    def convert_field(self, field, valfunc):
        fieldindex = self.fields.index(field)
        for feat in self:
            val = feat.row[fieldindex]
            feat.row[fieldindex] = valfunc(val)

    ### FILTERING ###

    def select(self, func):
        """Returns new filtered vectordata instance"""
        new = VectorData()
        new.fields = [field for field in self.fields]
        
        for feat in self:
            if func(feat):
                new.add_feature(feat.row, feat.geometry)

        return new

    def aggregate(self, key, geomfunc, fieldmapping=[]):
        # Aggregate values and geometries within key groupings
        # Allows a lot of customization
        # TODO: How is it different than manager.collapse()...?
        # TODO: Move to manager...?
        out = VectorData()
        out.fields = [fieldname for fieldname,_,_ in fieldmapping]

        from . import sql
        
        for feats in sql.groupby(self, key=key):
            row,geom = sql.aggreg(feats, aggregfuncs=fieldmapping, geomfunc=geomfunc)
            out.add_feature(row=row, geometry=geom)

        return out

    def duplicates(self, subkey=None, fieldmapping=[]):
        # groups duplicate geometries
        # TODO: Move to manager...?
        if subkey:
            # additional subgrouping based on eg attributes
            keywrap = lambda f: (f.geometry, subkey(f))
        else:
            # only by geometry
            keywrap = lambda f: f.geometry
            
        geomfunc = lambda items: items[0].geometry # since geometries are same within each group, pick first one
        out = self.aggregate(keywrap, geomfunc=geomfunc, fieldmapping=fieldmapping)
        
        return out

    def intersections(self):
        # cuts every feature by the intersections with all other features
        if not hasattr(self, "spindex"):
            self.create_spatial_index()
        
        out = VectorData()
        out.type = self.type
        out.fields = list(self.fields)
        geoms = dict(((f.id,f.get_shapely()) for f in self))


        def getisecs(g, geoms):
            isecs = []
            for og in geoms:
                #if og.area < 0.001: continue # this somehow makes it work....????
                if id(og) != id(g):
                    #print "testing", id(g), id(og)
                    isec_bool = og.equals(g) or (og.intersects(g) and not og.touches(g)) #og.crosses(g) or og.contains(g) or og.within(g) # not those that touch or equals
                    if isec_bool:
                        isec = g.intersection(og)

                        # sifting through dongles etc approach
##                        incl = []
##                        if isec.geom_type == "GeometryCollection":
##                            # only get same types, ie ignore dongles etc
##                            incl.extend([sub for sub in isec.geoms if out.type in sub.geom_type])
##                        elif out.type in isec.geom_type:
##                            # only if same type
##                            incl.append(isec)
##                        #viewisecs(g, [og], "pair isec = %s, include = %s" % (isec_bool,bool(incl)) )
##                        for sub in incl:
##                            #REMEMBER: this is only the immediate pairwise isecs, and might be further subdivided
##                            #viewisecs(g, [og], "pair isec = %s" % isec_bool)
##                            print repr(sub)
##                            isecs.append( sub )

                        # only pure approach
                        #print repr(isec)
                        if out.type in isec.geom_type:
                            #print "included for next step"
                            isecs.append(isec)
                            
##                        else:
##                            ###isecs.append(og)
##                            if hasattr(isec, "geoms"):
##                                for i in isec.geoms:
##                                    if out.type in i.geom_type and i.area >= 0.0001:
##                                        print str(i)[:200]
##                                        viewisecs(i, [], str(i.area) + " inside geomcollection, valid = %s" % i.is_valid)
##                                #viewisecs(og, [i for i in isec.geoms if out.type in i.geom_type], "wrong type")

                    else:
                        pass #viewisecs(g, [og], "isec_bool False")
                            
            return isecs

        DEBUG = False

        def viewisecs(g=None, isecs=None, title="[Title]"):
            if DEBUG: 
                from ..renderer import Map, Color
                mapp = Map(width=1000, height=1000, title=title)

                if isecs:
                    d = VectorData()
                    d.fields = ["dum"]
                    for i in isecs:
                        d.add_feature([1], i.__geo_interface__)
                    mapp.add_layer(d, fillcolor="blue")

                if g:
                    gd = VectorData()
                    gd.fields = ["dum"]
                    gd.add_feature([1], g.__geo_interface__)
                    mapp.add_layer(gd, fillcolor=Color("red",opacity=155))

                mapp.zoom_auto()
                mapp.view()

##        finals = []
##        compare = [f.get_shapely() for f in self]
##        for feat in self:
##            print feat
##            geom = geoms[feat.id]
##            compare = getisecs(geom, compare)
##            for sub in compare:
##                finals.append((feat,sub))
##        for feat,geom in finals:
##            out.add_feature(feat.row, geom.__geo_interface__)

        def process(isecs):
            parts = []
            for g in isecs:
                subisecs = getisecs(g, isecs)
                viewisecs(g, [], "getting subisecs of g")
                viewisecs(None, isecs, "compared to ...")
                if not subisecs:
                    viewisecs(g, [], "node (g) reached, adding" )
                    parts += [g]
                elif len(subisecs) == 1:
                    viewisecs(subisecs[0], [], "node (subisec) reached, adding" )
                    parts += [subisecs[0]]
                else:
                    viewisecs(None, subisecs, "going deeper, len = %s" % len(subisecs) )
                    parts += process(subisecs)
                    #viewisecs(g, subisecs, str(len(subisecs)) + " were returned as len = %s" % len(parts) )
            return parts

        for i,feat in enumerate(self):
            #if feat["CNTRY_NAME"] != "Russia": continue
            #if i >= 10:
            #    return out
            print feat
            geom = geoms[feat.id]
            top_isecs = [geoms[otherfeat.id] for otherfeat in self.quick_overlap(feat.bbox)]
            
            #print self.select(lambda f:f["CNTRY_NAME"]=="USSR")
            #top_isecs = [next((f.get_shapely() for f in self.select(lambda f:f["CNTRY_NAME"]=="USSR")))]
            #print "spindex",top_isecs
            #from ..renderer import Color
            #self.select(lambda f:f["CNTRY_NAME"]=="USSR").view(1000,1000,flipy=1,fillcolor=Color("red",opacity=155))
            #viewisecs(geom, top_isecs, "spindex to be tested for isecs")
            
            top_isecs = getisecs(geom, top_isecs)
            print "top_isecs",top_isecs
            viewisecs(geom, top_isecs, "spindex verified, len = %s" % len(top_isecs) )
            parts = process(top_isecs)
            for g in parts:
                print "adding", id(g)
                #viewisecs(g, [], "final isec")
                out.add_feature(feat.row, g.__geo_interface__)
        

##        for feat in self:
##            print feat
##            geom = geoms[feat.id]
##            # find all othergeoms that 
##            othergeoms = (geoms[f.id] for f in self.quick_overlap(feat.bbox))
##            othergeoms = [og for og in othergeoms if og.intersects(geom)]
##            for othergeom in othergeoms:
##                intsec = geom.intersection(othergeom)
##                if not intsec.is_empty and self.type in intsec.geom_type:
##                    print intsec.geom_type
##                    out.add_feature(feat.row, intsec.__geo_interface__)
##                    out.view(1000, 1000, flipy=1)


##        def cutup(geom, othergeoms):
##            parts = []
##            for othergeom in othergeoms:
##                # add intsecs
##                if geom != othergeom and geom.intersects(othergeom):
##                    intsec = geom.intersection(othergeom)
##                    if not intsec.is_empty:
##                        parts.append(intsec)
##            # add diff
##            diff = geom.difference(shapely.ops.cascaded_union(parts))
##            if not diff.is_empty:
##                parts.append(diff)
##            return parts
##
##        def subparts(geoms):
##            subs = []
##            for geom in geoms:
##                subs += cutup(geom, geoms)
##            return subs
##
##        def recur(geoms):
##            prevparts = []
##            parts = subparts(geoms)
##            while len(parts) != len(prevparts):
##                print len(parts)
##                prevparts = list(parts)
##                parts = subparts(parts)
##                break
##            return parts
##                
##        for feat in self:
##            geom = geoms[feat.id]
##            # find all othergeoms that 
##            othergeoms = (geoms[f.id] for f in self.quick_overlap(feat.bbox))
##            othergeoms = [og for og in othergeoms if og.intersects(geom)]
##            print feat
##            parts = recur([geom]+othergeoms)
##            print len(parts)


##        def flatten(geom):
##            if "Multi" in geom.geom_type:
##                for g in geom.geoms:
##                    yield g
##            else:
##                yield geom
##        for feat in self:
##            geom = geoms[feat.id]
##            # find all othergeoms that 
##            othergeoms = []
##            for otherfeat in self.quick_overlap(feat.bbox):
##                if otherfeat == feat: continue
##                if not geoms[otherfeat.id].intersects(geom): continue
##                othergeoms += list(flatten(geoms[otherfeat.id]))
##            # combine into one so only have to make one spatial test
##            if "Polygon" in self.type:
##                othergeom = shapely.geometry.MultiPolygon(othergeoms)
##            elif "LineString" in self.type:
##                othergeom = shapely.geometry.MultiLineString(othergeoms)
##            elif "Point" in self.type:
##                othergeom = shapely.geometry.MultiPoint(othergeoms)
##            else:
##                raise Exception()
##            print all((g.is_valid for g in othergeoms))
##            print othergeom.is_valid
##            # add intsecs
##            intsec = geom.intersection(othergeom)
##            if not intsec.is_empty:
##                for g in flatten(intsec):
##                    out.add_feature(feat.row, g)
##            # add diffs
##            diff = geom.difference(othergeom)
##            if not diff.is_empty:
##                for g in flatten(diff):
##                    out.add_feature(feat.row, g)

        return out

    def join(self, other, key, fieldmapping=[], keepall=True):
        # NOTE: key can be a single fieldname or function that returns the link for both tables, or a left-right key pair. 
        # TODO: enable multiple join conditions in descending priority, ie key can be a list of keys, so looks for a match using the first key, then the second, etc, until a match is found.
        # TODO: Move to manager...?
        out = VectorData()
        out.fields = list(self.fields)
        out.fields += (field for field in other.fields if field not in self.fields)
        out.fields += (fieldtup[0] for fieldtup in fieldmapping if fieldtup[0] not in out.fields)

        from . import sql

        if isinstance(key, (list,tuple)) and len(key) == 2:
            k1,k2 = key
        else:
            k1 = k2 = key # same key for both
        key1 = k1 if hasattr(k1,"__call__") else lambda f:f[k1]
        key2 = k2 if hasattr(k2,"__call__") else lambda f:f[k2]
        
        fieldmapping_default = [(field,lambda f,field=field:f[field],"first") for field in other.fields if field not in self.fields]
        fs,vfs,afs = zip(*fieldmapping) or [[],[],[]]
        
        def getfm(item):
            if item[0] in fs:
                return fieldmapping[fs.index(item[0])]
            else:
                return item
        fieldmapping_old = fieldmapping
        fieldmapping = [getfm(item) for item in fieldmapping_default]
        fieldmapping += (item for item in fieldmapping_old if item[0] not in self.fields and item[0] not in other.fields)
        print fieldmapping

        def grouppairs(data1, key1, data2, key2):
            # create hash table
            # inspired by http://rosettacode.org/wiki/Hash_join#Python
            hsh = dict()
            for keyval,f2s in itertools.groupby(sorted(data2,key=key2), key=key2):
                aggval = sql.aggreg(f2s, aggregfuncs=fieldmapping)
                hsh[keyval] = aggval
            # iterate join
            for f1 in data1:
                keyval = key1(f1)
                if keyval in hsh:
                    f2row = hsh[keyval]
                    yield f1,f2row
                elif keepall:
                    f2row = ("" for f in fieldmapping)
                    yield f1,f2row

        for pair in grouppairs(self, key1, other, key2):
            f1,f2row = pair
            row = list(f1.row)
            row += f2row
            out.add_feature(row=row, geometry=f1.geometry)

        return out
    

##        from . import sql
##
##        groupbydata = self
##        valuedata = other
##        def _condition(item):
##            f1,f2 = item
##            return condition(f1,f2)
##
##        if not fieldmapping:
##            fieldmapping = [ (field, lambda (f1,f2),field=field: f2[field], "first")
##                            for field in other.fields
##                             if field not in self.fields]
##
##        # add fields
##        out.fields = list(groupbydata.fields)
##        out.fields.extend([name for name,valfunc,aggfunc in fieldmapping])
##
##        # loop
##        for groupfeat in groupbydata:
##            newrow = list(groupfeat.row)
##            geoj = groupfeat.geometry
##
##            # aggregate
##            combinations = ((groupfeat,valfeat) for valfeat in valuedata)
##            matches = sql.where(combinations, _condition)
##            newrow.extend( sql.aggreg(matches, fieldmapping) )
##
##            # add
##            out.add_feature(newrow, geoj)
##
##        return out        
            
##        outvec.fields = self.fields + other.fields
##        
##        for feat1 in self:
##            anymatch = False
##            
##            for feat2 in other:
##                match = condition(feat1,feat2)
##                
##                if match:
##                    anymatch = True
##                    row = feat1.row + feat2.row
##                    outvec.add_feature(row=row, geometry=feat1.geometry)
##
##            if not anymatch and keepall:
##                row = feat1.row + ["" for _ in range(len(feat2.row))]
##                outvec.add_feature(row=row, geometry=feat1.geometry)
##
##        return outvec
                

    ### ACCESS TO ADVANCED METHODS FROM INTERNAL MODULES ###

    @property
    def manage(self):
        from . import manager
        return _ModuleFuncsAsClassMethods(self, manager)

    @property
    def analyze(self):
        from . import analyzer
        return _ModuleFuncsAsClassMethods(self, analyzer)

    @property
    def convert(self):
        from . import converter
        return _ModuleFuncsAsClassMethods(self, converter)


    ###### SPATIAL INDEXING #######

    def create_spatial_index(self):
        """Allows quick overlap search methods"""
        self.spindex = rtree.index.Index()
        for feat in self:
            if feat.geometry:
                self.spindex.insert(feat.id, feat.bbox)
   
    def quick_overlap(self, bbox):
        """
        Quickly get features whose bbox overlap the specified bbox via the spatial index.
        """
        if not hasattr(self, "spindex"):
            raise Exception("You need to create the spatial index before you can use this method")
        # ensure min,min,max,max pattern
        xs = bbox[0],bbox[2]
        ys = bbox[1],bbox[3]
        bbox = [min(xs),min(ys),max(xs),max(ys)]
        # return generator over results
        overlaps = self.spindex.intersection(bbox)
        return (self[id] for id in overlaps)

    def quick_disjoint(self, bbox):
        """
        Quickly get features whose bbox do -not- overlap the specified bbox via the spatial index.
        """
        if not hasattr(self, "spindex"):
            raise Exception("You need to create the spatial index before you can use this method")
        # ensure min,min,max,max pattern
        xs = bbox[0],bbox[2]
        ys = bbox[1],bbox[3]
        bbox = [min(xs),min(ys),max(xs),max(ys)]
        # return generator over results
        overlaps = set((id for id in self.spindex.intersection(bbox)))
        allids = set(self.features.keys())
        disjoint = allids.difference(overlaps)
        return (self[id] for id in disjoint)

    def quick_nearest(self, bbox, n=1):
        """
        Quickly get n features whose bbox are nearest the specified bbox via the spatial index.
        """
        if not hasattr(self, "spindex"):
            raise Exception("You need to create the spatial index before you can use this method")
        # ensure min,min,max,max pattern
        xs = bbox[0],bbox[2]
        ys = bbox[1],bbox[3]
        bbox = [min(xs),min(ys),max(xs),max(ys)]
        # return generator over results
        within = self.spindex.nearest(bbox, num_results=n)
        return (self[id] for id in within)
        
    ###### GENERAL #######

    def save(self, savepath, **kwargs):
        fields = self.fields
        rowgeoms = ((feat.row,feat.geometry) for feat in self)
        rows, geometries = itertools.izip(*rowgeoms)
        saver.to_file(fields, rows, geometries, savepath, **kwargs)

    def copy(self):
        new = VectorData()
        new.fields = [field for field in self.fields]
        featureobjs = (Feature(new, feat.row, feat.geometry) for feat in self )
        new.features = OrderedDict([ (feat.id,feat) for feat in featureobjs ])
        if hasattr(self, "spindex"): new.spindex = self.spindex.copy()
        return new

    def inspect(self, fields=None, maxvals=30):
        """Returns a dict of all fields and unique values for each."""
        # TODO: Allow only some fields
        # TODO: Maybe provide stats for numeric fields...
        cols = dict(zip(self.fields, zip(*self)))
        for field,vals in cols.items():
            uniqvals = set(vals)
            cols[field] = list(sorted(uniqvals))[:maxvals]

        import pprint
        return "Vector data contents:\n" + pprint.pformat(cols, indent=4)
    
    def render(self, width, height, bbox=None, flipy=True, **styleoptions):
        from .. import renderer
        lyr = renderer.VectorLayer(self, **styleoptions)
        lyr.render(width=width, height=height, bbox=bbox, flipy=flipy)
        return lyr

    def view(self, width, height, bbox=None, flipy=True, **styleoptions):
        lyr = self.render(width, height, bbox, flipy, **styleoptions)
        
        import Tkinter as tk
        import PIL.ImageTk
        
        app = tk.Tk()
        tkimg = PIL.ImageTk.PhotoImage(lyr.img)
        lbl = tk.Label(image=tkimg)
        lbl.tkimg = tkimg
        lbl.pack()
        app.mainloop()


    
