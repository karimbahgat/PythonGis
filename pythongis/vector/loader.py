
# import builtins
import os
import csv
import codecs
import itertools

# import fileformat modules
import shapefile as pyshp
import pygeoj

from ..exceptions import UnknownFileError


def from_file(filepath, encoding="utf8", **kwargs):

    # TODO: for geoj and delimited should detect and force consistent field types in similar manner as when saving

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
        rowgeoms = itertools.izip(rows, geometries)
        
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
        rowgeoms = itertools.izip(rows, geometries)

        # load crs
        crs = geojfile.crs

    # table files without geometry
    elif filepath.endswith((".txt",".csv",".xls",".xlsx")):

        # txt or csv
        if filepath.endswith((".txt",".csv")):
            delimiter = kwargs.get("delimiter")
            fileobj = open(filepath, "rU")
            if delimiter is None:
                dialect = csv.Sniffer().sniff(fileobj.read())
                fileobj.seek(0)
                rows = csv.reader(fileobj, dialect)
            else:
                rows = csv.reader(fileobj, delimiter=delimiter)
            def parsestring(string):
                try:
                    val = float(string.replace(",","."))
                    if val.is_integer():
                        val = int(val)
                    return val
                except:
                    if string.upper() == "NULL":
                        return None
                    else:
                        return string.decode(encoding)
            rows = ([parsestring(cell) for cell in row] for row in rows)
            fields = next(rows)

        # excel
        elif filepath.endswith((".xls",".xlsx")):
            if filepath.endswith(".xls"):
                import xlrd
                wb = xlrd.open_workbook(filepath, encoding_override=encoding, on_demand=True)
                if "sheet" in kwargs:
                    sheet = wb.sheet_by_name(kwargs["sheet"])
                else:
                    sheet = wb.sheet_by_index(0)
                rows = ([cell.value for cell in row] for row in sheet.get_rows())
                fields = next(rows)
                
            elif filepath.endswith(".xlsx"):
                raise NotImplementedError()
        
        geokey = kwargs.get("geokey")
        xfield = kwargs.get("xfield")
        yfield = kwargs.get("yfield")
        
        if geokey:
            rowgeoms = ((row,geokey(dict(zip(fields,row)))) for row in rows)
            
        elif xfield and yfield:
            def xygeoj(row):
                rowdict = dict(zip(fields,row))
                x,y = rowdict[xfield],rowdict[yfield]
                try: x,y = float(x),float(y)
                except: x,y = float(x.replace(",",".")),float(y.replace(",","."))
                geoj = {"type":"Point", "coordinates":(x,y)}
                return geoj
            rowgeoms = ((row,xygeoj(row)) for row in rows)
            
        else:
            rowgeoms = ((row,None) for row in rows)
            
        crs = None
    
    else:
        raise UnknownFileError("Could not create vector data from the given filepath: the filetype extension is either missing or not supported")

    # filter if needed
    if select:
        rowgeoms = ( (row,geom) for row,geom in rowgeoms if select(dict(zip(fields,row))) )

    # load to memory in lists
    rows,geometries = itertools.izip(*rowgeoms)
    rows = list(rows)
    geometries = list(geometries)

    return fields, rows, geometries, crs






