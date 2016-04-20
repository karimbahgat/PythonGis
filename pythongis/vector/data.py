
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

    @property
    def bbox(self):
        xmins, ymins, xmaxs, ymaxs = itertools.izip(*(feat.bbox for feat in self if feat.geometry))
        xmin, xmax = min(xmins), max(xmaxs)
        ymin, ymax = min(ymins), max(ymaxs)
        bbox = (xmin, ymin, xmax, ymax)
        return bbox

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

    def compute(self, field, func):
        if field not in self.fields:
            self.add_field(field)
        for feat in self:
            feat[field] = func(feat)

    def drop_field(self, field):
        fieldindex = self.fields.index(field)
        del self.fields[fieldindex]
        for feat in self:
            del feat.row[fieldindex]

    def drop_fields(self, fields):
        for f in fields:
            self.drop_field(f)

    def keep_fields(self, fields):
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
        out = VectorData()
        out.fields = [fieldname for fieldname,_,_ in fieldmapping]

        from . import sql
        
        for feats in sql.groupby(self, key=key):
            row,geom = sql.aggreg(feats, aggregfuncs=fieldmapping, geomfunc=geomfunc)
            out.add_feature(row=row, geometry=geom)

        return out

    def aggregate_duplicate_geoms(self, subkey=None, fieldmapping=[]):
        # group within unique geometries
        if subkey:
            # additional subgrouping within identical geometries
            keywrap = lambda f: (f.geometry, subkey(f))
        else:
            # only by geometry
            keywrap = lambda f: f.geometry
            
        geomfunc = lambda items: items[0].geometry # since geometries are same within each group, pick first one
        out = self.aggregate(keywrap, geomfunc=geomfunc, fieldmapping=fieldmapping)
        
        return out

    def join(self, other, k1, k2, fieldmapping=[], keepall=True): 
        out = VectorData()
        out.fields = list(self.fields)
        out.fields += (field for field in other.fields if field not in self.fields)

        from . import sql

        key1 = k1 if hasattr(k1,"__call__") else lambda f:f[k1]
        key2 = k2 if hasattr(k2,"__call__") else lambda f:f[k2]
        
        _fieldmapping = [(field,lambda f,field=field:f[field],"first") for field in other.fields if field not in self.fields]
        fs,vfs,afs = zip(*fieldmapping) or [[],[],[]]
        
        def getfm(item):
            if item[0] in fs:
                return fieldmapping[fs.index(item[0])]
            else:
                return item
        fieldmapping = [getfm(item) for item in _fieldmapping]

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
                    f2row = ("" for f in other.fields if f not in self.fields)
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
        results = self.spindex.intersection(bbox)
        return (self[id] for id in results)

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
        results = self.spindex.nearest(bbox, num_results=n)
        return (self[id] for id in results)
        
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

    def inspect(self, maxvals=30):
        """Returns a dict of all fields and unique values for each."""
        cols = dict(zip(self.fields, zip(*self)))
        for field,vals in cols.items():
            uniqvals = set(vals)
            cols[field] = list(sorted(uniqvals))[:maxvals]

        import pprint
        return "Vector data contents:\n" + pprint.pformat(cols, indent=4)
    
    def render(self, width, height, bbox=None, flipy=False, **styleoptions):
        from .. import renderer
        lyr = renderer.VectorLayer(self, **styleoptions)
        lyr.render(width=width, height=height, bbox=bbox, flipy=flipy)
        return lyr

    def view(self, width, height, bbox=None, flipy=False, **styleoptions):
        lyr = self.render(width, height, bbox, flipy, **styleoptions)
        
        import Tkinter as tk
        import PIL.ImageTk
        
        app = tk.Tk()
        tkimg = PIL.ImageTk.PhotoImage(lyr.img)
        lbl = tk.Label(image=tkimg)
        lbl.tkimg = tkimg
        lbl.pack()
        app.mainloop()        


    
