import sys, os, itertools, operator
from collections import OrderedDict
import datetime



import shapely
from shapely.geometry import asShape as geoj2geom
from shapely.geometry import mapping as geom2geoj
import rtree



from . import loader
from . import saver




class Feature:
    def __init__(self, table, row, geometry, id=None):
        "geometry must be a geojson dictionary or a shapely geometry instance"
        self._table = table
        self.row  = list(row)
        
        if isinstance(geometry, dict): bbox = geometry.get("bbox")
        else: bbox = None
        self._cached_bbox = bbox

        self.geometry = geometry.copy()

        # ensure it is same geometry type as parent
        geotype = self.geometry["type"]
        if self._table.type: 
            if "Point" in geotype and self._table.type == "Point": pass
            elif "LineString" in geotype and self._table.type == "LineString": pass
            elif "Polygon" in geotype and self._table.type == "Polygon": pass
            else: raise TypeError("Each feature geometry must be of the same type as the file it is attached to")
        else: self._table.type = self.geometry["type"].replace("Multi", "")
        
        if id == None: id = next(self._table._id_generator)
        self.id = id

    def __getitem__(self, i):
        if isinstance(i, (str,unicode)):
            i = self._table.fields.index(i)
        return self.row[i]

    def __setitem__(self, i, setvalue):
        if isinstance(i, (str,unicode)):
            i = self._table.fields.index(i)
        self.row[i] = setvalue

    @property
    def bbox(self):
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

    def copy(self):
        geoj = self.geometry
        if self._cached_bbox: geoj["bbox"] = self._cached_bbox
        return Feature(self._table, self.row, geoj)




def ID_generator():
    i = 0
    while True:
        yield i
        i += 1



class GeoTable:
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
        print self.crs

    def __len__(self):
        return len(self.features)

    def __iter__(self):
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
        xmins, ymins, xmaxs, ymaxs = itertools.izip(*(feat.bbox for feat in self))
        xmin, xmax = min(xmins), max(xmaxs)
        ymin, ymax = min(ymins), max(ymaxs)
        bbox = (xmin, ymin, xmax, ymax)
        return bbox

    ### DATA ###

    def add_feature(self, row, geometry):
        feature = Feature(self, row, geometry)
        self[feature.id] = feature

    ###### SPATIAL INDEXING #######

    def create_spatial_index(self):
        self.spindex = rtree.index.Index()
        for feat in self:
            self.spindex.insert(feat.id, feat.bbox)
    
    def quick_overlap(self, bbox):
        if not hasattr(self, "spindex"): raise Exception("You need to create the spatial index before you can use this method")
        # ensure min,min,max,max pattern
        xs = bbox[0],bbox[2]
        ys = bbox[1],bbox[3]
        bbox = [min(xs),min(ys),max(xs),max(ys)]
        # return generator over results
        results = self.spindex.intersection(bbox)
        return (self[id] for id in results)

    def quick_nearest(self, bbox, n=1):
        if not hasattr(self, "spindex"): raise Exception("You need to create the spatial index before you can use this method")
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
        new = GeoTable()
        new.fields = [field for field in self.fields]
        featureobjs = (Feature(new, feat.row, feat.geometry) for feat in self )
        new.features = OrderedDict([ (feat.id,feat) for feat in featureobjs ])
        if hasattr(self, "spindex"): new.spindex = self.spindex.copy()
        return new
























    ###### FIELDS #######

    def addfield(self, field):
        self.fields.append(field)
        for row in self.rows:
            row.append(MISSING)

    def keepfields(self, *fields):
        pass

    def dropfields(self, *fields):
        pass

    ###### SELECT #######

    def iter_select(self, query):
        "return a generator of True False for each row's query result"
        # MAYBE ALSO ADD SUPPORT FOR SENDING A TEST FUNCTION
        for row in self:
            # make fields into vars
            for field in self.fields:
                value = row[self.fields.index(field)]
                if isinstance(value, (unicode,str)):
                    value = '"""'+str(value).replace('"',"'")+'"""'
                elif isinstance(value, (int,float)):
                    value = str(value)
                code = "%s = %s"%(field,value)
                exec(code)
            # run and retrieve query value
            yield eval(query)

    def select(self, query):
        outtable = self.copy(copyrows=False)
        for row,keep in zip(self,self.iter_select(query)):
            if keep:
                outtable.append(row)
        return outtable

    def exclude(self, query):
        outtable = Table()
        for row,drop in zip(self,self.iter_select(query)):
            if not drop:
                outtable.append(row)
        return outtable

    ###### GROUP #######

    def split(self, splitfields):
        """
        Sharp/distinct groupings.
        """
        fieldindexes = [self.fields.index(field) for field in splitfields]
        temprows = sorted(self.rows, key=operator.itemgetter(*fieldindexes))
        for combi,rows in itertools.groupby(temprows, key=operator.itemgetter(*fieldindexes) ):
            table = self.copy(copyrows=False)
            table.rows = list(rows)
            table.name = str(combi)
            yield table

    def aggregate(self, groupfields, fieldmapping=[]):
        """
        ...choose to aggregate into a summary value, OR into multiple fields (maybe not into multiple fields, for that use to_fields() afterwards...
        ...maybe make flexible, so aggregation can be on either unique fields, or on an expression or function that groups into membership categories (if so drop membership() method)...
        """
        if fieldmapping: aggfields,aggtypes = zip(*fieldmapping)
        aggfunctions = dict([("count",len),
                             ("sum",sum),
                             ("max",max),
                             ("min",min),
                             ("average",stats.average),
                             ("median",stats.median),
                             ("stdev",stats.stdev),
                             ("most common",stats.most_common),
                             ("least common",stats.least_common) ])
        outtable = self.copy(copyrows=False)
        fieldindexes = [self.fields.index(field) for field in groupfields]
        temprows = sorted(self.rows, key=operator.itemgetter(*fieldindexes))
        for combi,rows in itertools.groupby(temprows, key=operator.itemgetter(*fieldindexes) ):
            if not isinstance(combi, tuple):
                combi = tuple([combi])
            # first the groupby values
            newrow = list(combi)
            # then the aggregation values
            if fieldmapping:
                columns = zip(*rows)
                selectcolumns = [columns[self.fields.index(field)] for field in aggfields]
                for aggtype,values in zip(aggtypes,selectcolumns):
                    aggfunc = aggfunctions[aggtype]
                    aggvalue = aggfunc(values)
                    newrow.append(aggvalue)
            outtable.append(newrow)
        outtable.fields = groupfields
        if fieldmapping: outtable.fields.extend(aggfields)
        return outtable

    ###### CREATE #######

    def compute(self, fieldname, expression, query=None):
        # NOTE: queries and expressions currently do not validate
        # that value types are of the same kind, eg querying if a number
        # is bigger than a string, so may lead to weird results or errors. 
        if not fieldname in self.fields:
            self.addfield(fieldname)
        expression = "result = %s" % expression
        for row in self:
            # make fields into vars
            for field in self.fields:
                value = row[self.fields.index(field)]
                if isinstance(value, (unicode,str)):
                    value = '"""'+str(value).replace('"',"'")+'"""'
                elif isinstance(value, (int,float)):
                    value = str(value)
                code = "%s = %s"%(field,value)
                exec(code)
            # run and retrieve expression value          
            if not query or (eval(query) == True):
                exec(expression)
                row[self.fields.index(fieldname)] = result
        return self

    ###### CONNECT #######

    def join(self, othertable, query):
        """
        ...
        """
        pass

    def relate(self, othertable, query):
        """maybe add a .relates attribute dict to each row,
        with each relate dict entry being the unique tablename of the other table,
        containing another dictionary with a "query" entry for that relate,
        and a "links" entry with a list of rows pointing to the matching rows in the other table.
        """
        pass










