import sys, os, itertools, operator
import datetime



import shapely
from shapely.geometry import asShape as geoj2geom
from shapely.geometry import mapping as geom2geoj
import rtree



from . import loader




class Feature:
    def __init__(self, table, row, geometry):
        "geometry must be a geojson dictionary or a shapely geometry instance"
        self._table = table
        self.row  = list(row)
        if isinstance(geometry, dict): geometry = geoj2geom(geometry)
        self.geometry = geometry # maybe need to copy geometry?
        self._cached_bbox = None

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
            self._cached_bbox = self.geometry.bounds
        return self._cached_bbox

    def copy(self):
        return Feature(self._table, self.row, self.geometry)







class GeoTable:
    def __init__(self, filepath=None):
        if filepath:
            fields,rows,geometries = loader.from_file(filepath)
        else:
            fields,rows,geometries = [],[],[]
            
        self.fields = fields
        self.features = [Feature(self,row,geom) for row,geom in itertools.izip(rows,geometries)]
        self.create_spatial_index()

    def __len__(self):
        return len(self.features)

    def __iter__(self):
        for feat in self.features:
            yield feat

    def __getitem__(self, i):
        """
        Get one or more Features of data.
        """
        return self.features[i]

    @property
    def bbox(self):
        xmins, xmaxs, ymins, ymaxs = itertools.izip(*(feat.bbox for feat in self))
        xmin, xmax = min(xmins), max(xmaxs)
        ymin, ymax = min(ymins), max(ymaxs)
        bbox = (xmin, ymin, xmax, ymax)
        return bbox

    ###### SPATIAL INDEXING #######

    def create_spatial_index(self):
        self.spindex = rtree.index.Index()
        i = 0
        for feat in self:
            self.spindex.insert(i, feat.bbox, obj=feat)
            i += 1
    
    def intersecting(self, bbox):
        results = self.spindex.intersection(bbox, objects="raw")
        return results

    def nearest(self, bbox):
        results = self.spindex.nearest(bbox, objects="raw")
        return results

    ###### GENERAL #######

    def save(self, savepath, **kwargs):
        fields = self.fields
        rowgeoms = ((feat.row,feat.geometry) for feat in self)
        rows, geometries = itertools.izip(*rowgeoms)
        saver.to_file(fields, rows, geometries, savepath, **kwargs)

    def copy(self):
        new = GeoTable()
        new.fields = [field for field in self.fields]
        new.features = [Feature(new,feat.row,feat.geom,feat.bbox) for feat in self.features]
        new.bbox = self.bbox
        new.create_spindex()
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










