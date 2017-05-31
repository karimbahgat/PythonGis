
# import builtins
import sys, os, itertools, operator, math
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





def is_missing(val):
    return val is None or (isinstance(val, float) and math.isnan(val))






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

    def iter_points(self):
        """Yields every point in the geometry as a flat generator,
        useful for quick inspecting of dimensions so don't have to
        worry about nested coordinates and geometry types"""
        geoj = self.geometry
        if not geoj:
            yield None

        geotype = self.geometry["type"]
        coords = self.geometry["coordinates"]
        
        if geotype == "Point":
            yield geoj["coordinates"]
        elif geotype in ("MultiPoint","LineString"):
            for p in coords:
                yield p
        elif geotype == "MultiLineString":
            for line in coords:
                for p in line:
                    yield p
        elif geotype == "Polygon":
            for ext_or_hole in coords:
                for p in ext_or_hole:
                    yield p
        elif geotype == "MultiPolygon":
            for poly in coords:
                for ext_or_hole in poly:
                    for p in ext_or_hole:
                        yield p

    def transform(self, func):
        """
        Transforms the feature geometry in place.
        
        - func: a function that takes a flat list of points, does something, and returns them
        """
        geoj = self.geometry
        if not geoj:
            return None

        geotype = geoj["type"]
        coords = geoj["coordinates"]
        
        if geotype == "Point":
            geoj["coordinates"] = func([coords])[0]
        elif geotype in ("MultiPoint","LineString"):
            geoj["coordinates"] = func(coords)
        elif geotype == "MultiLineString":
            geoj["coordinates"] = [func(line)
                                   for line in coords]
        elif geotype == "Polygon":
            geoj["coordinates"] = [func(ext_or_hole)
                                   for ext_or_hole in coords]
        elif geotype == "MultiPolygon":
            geoj["coordinates"] = [[func(ext_or_hole)
                                    for ext_or_hole in poly]
                                   for poly in coords]
            
        self._cached_bbox = None
        
        return True

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


def Name_generator():
    i = 1
    while True:
        yield "Untitled%s" % i
        i += 1


NAMEGEN = Name_generator()



class VectorData:
    def __init__(self, filepath=None, type=None, name=None, fields=None, rows=None, geometries=None, features=None, crs=None, **kwargs):
        self.filepath = filepath
        self.name = name or filepath
        if not self.name:
            self.name = next(NAMEGEN)

        # type is optional and will make the features ensure that all geometries are of that type
        # if None, type enforcement will be based on first geometry found
        self.type = type
        
        if filepath:
            fields,rows,geometries,crs = loader.from_file(filepath, **kwargs)
        else:
            if features:
                rows,geometries = itertools.izip(*((feat.row,feat.geometry) for feat in features))
            else:
                rows = rows or []
                geometries = geometries or []
            fields = fields or []
            crs = crs or "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

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

    def __geo_interface__(self):
        """
        Returns geojson as feature collection, with crs, features, properties, etc. 
        """
        raise NotImplementedError()

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

    def sort(self, key, reverse=False):
        self.features = OrderedDict([ (feat.id,feat) for feat in sorted(self.features.values(), key=key, reverse=reverse) ])

    def add_feature(self, row, geometry=None):
        feature = Feature(self, row, geometry)
        self[feature.id] = feature
        return feature

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

    def interpolate(self, step):
        # maybe one for inserting new rows in between gaps
        # another for just filling missing values in between gaps
        # maybe it does both
        # and finally a separate for interpolating one value based on values in another...
        # ...
        pass

    def moving_window(self, n, fieldmapping, groupby=None):
        # general flexible method that cursors over a window of rows and runs arbitrary function on them
        for name,valfunc,statfunc in fieldmapping:
            if not name in self.fields:
                self.add_field(name)
        prevs = []

        from . import sql

        def calc(f, prevs, fieldmapping):
            prevs.append(f)
            if len(prevs) > n:
                prevs.pop(0)
            row = sql.aggreg(prevs, fieldmapping)
            for (name,_,_),val in zip(fieldmapping,row):
                f[name] = val

        if groupby:
            for _,feats in self.group(groupby):
                prevs = []
                for f in feats:
                    calc(f, prevs, fieldmapping)

        else:
            prevs = []
            for f in self:
                calc(f, prevs, fieldmapping)
        
        return self

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
                raise Exception("%s is not a field" % kf)
        for f in reversed(self.fields):
            if f not in fields:
                self.drop_field(f)

    def rename_field(self, oldname, newname):
        self.fields[self.fields.index(oldname)] = newname

    def convert_field(self, field, valfunc):
        fieldindex = self.fields.index(field)
        for feat in self:
            val = feat.row[fieldindex]
            feat.row[fieldindex] = valfunc(val)

    def inspect_field(self, field):
        """Returns more detailed stats unique values freq for a single field."""

        # TODO: split into multiple methods, eg field_stats vs field_values/frequencies
        # TODO: standardize table string formatting, eg as a vectordata.stringformat() method, and simply populate a stats vectordata table and call its method
        # TODO: sort freq table by percentages
        # TODO: fix unicode print error
        
        typ = self.field_type(field)
        getval = lambda v: v
        values = [f[field] for f in self]

        def getmissing(v):
            """Sets valid values to none so that only missing values are counted in stats"""
            v = is_missing(getval(v))
            v = True if v else None 
            return v

        from . import sql
        
        if typ in ("text",):
            printfields = ["", "frequency", "percent"]
            printrows = []

            for uniq in sorted(set(values)):
                freq = values.count(uniq)
                perc = freq / float(len(self)) * 100
                perc = "%.2f%%" % perc
                printrow = [uniq, freq, perc]
                printrows.append(printrow)
            
        elif typ in ("int","float"):
            printfields = ["", "type", "min/minority", "max/majority", "mean", "stdev", "missing"]
            printrows = []
            fieldmapping = [("min",getval,"min"),
                            ("max",getval,"max"),
                            ("mean",getval,"mean"),
                            #("stdev",getval,"stddev"),
                            ("missing",getmissing,"count"),]
            _min,_max,mean,missing = sql.aggreg(values, aggregfuncs=fieldmapping)
            missing = missing if missing else 0
            missing = "%s (%.2f%%)" % (missing, missing/float(len(self))*100 )
            printrow = [field, typ, _min, _max, mean, None, missing]
            printrows.append(printrow)

        # format outputstring
        outstring = "Inspecting field: '%s' \n" % field
        outstring += "type: %s \n" % typ
        outstring += "values: " + "\n"

        row_format = "{:>15}" * (len(printfields))
        outstring += row_format.format(*printfields) + "\n"
        for row in printrows:
            outstring += row_format.format(*row) + "\n"

        return outstring

    def histogram(self, field, width=None, height=None, bins=10):
        import pyagg
        import classypie
        values = [f[field] for f in self]

        bars = []
        for (_min,_max),group in classypie.split(values, breaks="equal", classes=bins):
            label = "%s to %s" % (_min,_max)
            count = len(group)
            bars.append((label,count))
            
        c = pyagg.graph.BarChart()
        c.add_category(name="Title...", baritems=bars)
        return c.draw() # draw returns the canvas

    def describe(self, *fields):
        """Returns table of fieldname, type, min/minority, max/majority, stdev, missing"""

        # TODO: maybe not use all those stats...

        printfields = ["", "type", "min/minority", "max/majority", "mean", "stdev", "missing"]
        printrows = []

        from . import sql
        if not fields:
            fields = self.fields
        
        for field in fields:
            
            values = [feat[field] for feat in self]
            typ = self.field_type(field)
            getval = lambda v: v
            
            def getmissing(v):
                """Sets valid values to none so that only missing values are counted in stats"""
                v = is_missing(getval(v))
                v = True if v else None 
                return v
            
            if typ in ("text",):
                fieldmapping = [("min/minority",getval,"minority"),
                                ("max/majority",getval,"majority"),
                                ("missing",getmissing,"count"),]
                minor,major,missing = sql.aggreg(values, aggregfuncs=fieldmapping)
                printrow = [field, typ, minor, major, None, None, missing]
                
            elif typ in ("int","float"):
                fieldmapping = [("min/minority",getval,"min"),
                                ("max/majority",getval,"max"),
                                ("mean",getval,"mean"),
                                #("stdev",getval,"stddev"),
                                ("missing",getmissing,"count"),]
                _min,_max,mean,missing = sql.aggreg(values, aggregfuncs=fieldmapping)
                missing = missing if missing else 0
                missing = "%s (%.2f%%)" % (missing, missing/float(len(self))*100 )
                printrow = [field, typ, _min, _max, mean, None, missing]
                
            printrows.append(printrow)

        # format outputstring
        outstring = "Describing vector data:" + "\n"
        outstring += "filepath: %s \n" % self.filepath
        outstring += "type: %s \n" % self.type
        outstring += "length: %s \n" % len(self) 
        outstring += "bbox: %s \n" % repr(self.bbox) if self.has_geometry else None       
        outstring += "fields:" + "\n"
        
        row_format = "{:>15}" * (len(printfields))
        outstring += row_format.format(*printfields) + "\n"
        for row in printrows:
            outstring += row_format.format(*row) + "\n"
            
        return outstring

    def field_type(self, field):
        """Returns field type of field based on its values (ignoring missing values)"""
        values = (f[field] for f in self)
        values = (v for v in values if not is_missing(v))
        # approach: at first assume int, if fails then assume float,
        # ...if fails then assume text and stop checking (lowest possible dtype)
        typ = "int"
        for v in values:
            # TODO: also detect other types eg datetime, etc
            try:
                v = float(v)
                if v.is_integer():
                    pass
                else:
                    typ = "float"
            except:
                typ = "text"
                break
        return typ

    ### FILTERING ###

    def get(self, func):
        """Iterates over features that meet filter conditions"""
        new = VectorData()
        new.fields = [field for field in self.fields]
        
        for feat in self:
            if func(feat):
                yield feat

    def group(self, key):
        for uid,feats in itertools.groupby(sorted(self, key=key), key=key):
            yield uid, list(feats)

    ### OTHER ###

    def select(self, func):
        """Returns new filtered VectorData instance"""
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

    def quick_nearest(self, bbox, n=None, radius=None):
        """
        Quickly get n features whose bbox are nearest the specified bbox via the spatial index.
        """
        # TODO: special handling if points data, might be faster to just test all.
        # ...
        
        if not hasattr(self, "spindex"):
            raise Exception("You need to create the spatial index before you can use this method")
        
        # ensure min,min,max,max pattern
        xs = bbox[0],bbox[2]
        ys = bbox[1],bbox[3]
        bbox = [min(xs),min(ys),max(xs),max(ys)]
        # return generator over results
        if not n:
            n = len(self)

        for id in self.spindex.nearest(bbox, num_results=n): # radius not yet respected
            feat = self[id]
            yield feat
           
##        if radius:
##            window = shapely.geometry.box(*bbox)
##            for id in self.spindex.nearest(bbox, num_results=n):
##                feat = self[id]
##                # bboxes are sorted by distance, so only yield while bbox is inside of radius
##                if window.distance(shapely.geometry.box(*feat.bbox)) <= radius:
##                    yield feat
##                else:
##                    break
##        else:
##            # TODO: if wanting to find x nearest regardless of distance, then we must sort by max bbox distance,
##            # then group by continuous intersectioning ones, and return from each group until n reached
##            box = shapely.geometry.box(*bbox)
##            def maxdist(otherfeat):
##                "get highest distance to any of the corners of bbox"
##                return max((box.distance(shapely.geometry.Point(*p)) for p in shapely.geometry.box(*otherfeat.bbox).coordinates))
##            feats = (self[id] for id in self.spindex.nearest(bbox, num_results=n))
##            sortfeats = (f for f in sorted(feats, key=maxdist))
##            i = 0
##            def grouped():
##                groupid = 0
##                prevfeat = None
##                for feat in sortfeats:
##                    if fsd:
##                        fdsf
##            for key,subfeats in sorted(sortfeats):
##                yield self[id]
        
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
        #if hasattr(self, "spindex"): new.spindex = self.spindex.copy() # NO SUCH METHOD
        return new
    
    def render(self, width=None, height=None, bbox=None, flipy=True, title="", background=None, **styleoptions):
        from .. import renderer
        mapp = renderer.Map(width, height, title=title, background=background)
        mapp.add_layer(self, **styleoptions)
        if bbox:
            mapp.zoom_bbox(*bbox)
        else:
            mapp.zoom_bbox(*mapp.layers.bbox)
        mapp.render_all()
        return mapp

    def browse(self):
        from .. import app
        win = app.builder.TableGUI()
        rows = (f.row for f in self)
        win.browser.table.populate(self.fields, rows)
        win.mainloop()

    def view(self, width=None, height=None, bbox=None, flipy=True, title="", background=None, **styleoptions):
        from .. import app
        mapp = self.render(width, height, bbox, flipy, title=title, background=background, **styleoptions)
        # make gui
        win = app.builder.MultiLayerGUI(mapp)
        win.mainloop()
        
##        mapp = self.render(width, height, bbox, flipy, **styleoptions)
##        
##        import Tkinter as tk
##        import PIL.ImageTk
##        
##        app = tk.Tk()
##        tkimg = PIL.ImageTk.PhotoImage(mapp.img)
##        lbl = tk.Label(image=tkimg)
##        lbl.tkimg = tkimg
##        lbl.pack()
##        app.mainloop()


    
