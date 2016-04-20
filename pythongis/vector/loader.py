
# import builtins
import os
import csv
import codecs
import itertools

# import fileformat modules
import shapefile as pyshp
import pygeoj


def from_file(filepath, encoding="utf8", **kwargs):

    select = kwargs.get("select")

    def decode(value):
        if isinstance(value, str): 
            return value.decode(encoding)
        else: return value
    
    # shapefile
    if filepath.endswith(".shp"):
        shapereader = pyshp.Reader(filepath, **kwargs) # TODO: does pyshp take kwargs?
        
        # load fields, rows, and geometries
        fields = [decode(fieldinfo[0]) for fieldinfo in shapereader.fields[1:]]
        rows = ( [decode(value) for value in record] for record in shapereader.iterRecords() )
        def getgeoj(obj):
            geoj = obj.__geo_interface__
            if hasattr(obj, "bbox"): geoj["bbox"] = list(obj.bbox)
            return geoj
        geometries = (getgeoj(shape) for shape in shapereader.iterShapes())
        
        # load projection string from .prj file if exists
        if os.path.lexists(filepath[:-4] + ".prj"):
            crs = open(filepath[:-4] + ".prj", "r").read()
        else: crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

    # geojson file
    elif filepath.endswith((".geojson",".json")):
        geojfile = pygeoj.load(filepath, encoding=encoding, **kwargs)

        # load fields, rows, and geometries
        fields = [field for field in geojfile.common_attributes]
        rows = ([feat.properties[field] for field in fields] for feat in geojfile)
        geometries = (feat.geometry.__geo_interface__ for feat in geojfile)

        # load crs
        crs = geojfile.crs

    # normal table file without geometry
    elif filepath.endswith((".txt",".csv")):
        delimiter = kwargs.get("delimiter")
        fileobj = open(filepath, "rU")
        if delimiter is None:
            dialect = csv.Sniffer().sniff(fileobj.read())
            fileobj.seek(0)
            rows = csv.reader(fileobj, dialect)
        else:
            rows = csv.reader(fileobj, delimiter=delimiter)
        rows = ([cell.decode(encoding) for cell in row] for row in rows)
        fields = next(rows)
        
        geokey = kwargs.get("geokey")
        xfield = kwargs.get("xfield")
        yfield = kwargs.get("yfield")
        
        if geokey:
            rows = list(rows) # needed so rowgen doesnt get consumed
            geometries = (geokey(dict(zip(fields,row))) for row in rows)
            
        elif xfield and yfield:
            rows = list(rows) # needed so rowgen doesnt get consumed
            def xygeoj(row):
                rowdict = dict(zip(fields,row))
                x,y = rowdict[xfield],rowdict[yfield]
                try: x,y = float(x),float(y)
                except: x,y = float(x.replace(",",".")),float(y.replace(",","."))
                geoj = {"type":"Point", "coordinates":(x,y)}
                return geoj
            geometries = (xygeoj(row) for row in rows)
            
        else:
            rows = list(rows)
            geometries = (None for _ in rows)
            
        crs = None
    
    else:
        raise Exception("Could not create vector data from the given filepath: the filetype extension is either missing or not supported")

    # filter if needed
    if select:
        rowgeoms = itertools.izip(rows, geometries)
        rowgeoms = ( (row,geom) for row,geom in rowgeoms if select(dict(zip(fields,row))) )
        rows,geometries = itertools.izip(*rowgeoms)

    # load to memory in lists
    rows = list(rows)
    geometries = list(geometries)

    return fields, rows, geometries, crs






