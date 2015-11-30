
from . import fileformats
from fileformats import shapefile as pyshp
from fileformats import pygeoj


import itertools


def to_file(fields, rows, geometries, filepath, encoding="utf8"):

    def encode(value):
        if isinstance(value, (float,int)): return value
        elif isinstance(value, unicode):
            return value.encode(encoding)
        else: return bytes(value)
    
    # shapefile
    if filepath.endswith(".shp"):
        # create writer
        shapewriter = pyshp.Writer()
        # add fields in correct fieldtype
        for fieldindex,fieldname in enumerate(fields):
            for row in rows:
                value = row[fieldindex]
                if value != "":
                    try:
                        # make nr fieldtype if content can be made into nr
                        float(value)
                        fieldtype = "N"
                        fieldlen = 16
                        decimals = 8
                    except:
                        # but turn to text if any of the cells cannot be made to float bc they are txt
                        fieldtype = "C"
                        fieldlen = 250
                        decimals = 0
                        break
                else:
                    # no values, just assume nr type
                    fieldtype = "N"
                    fieldlen = 16
                    decimals = 8
            # clean fieldname
            fieldname = fieldname.replace(" ","_")[:10]
            # write field
            shapewriter.field(fieldname.encode(encoding), fieldtype, fieldlen, decimals)

        # convert geojson to shape
        def geoj2shape(geoj):
            # create empty pyshp shape
            shape = pyshp._Shape()
            # set shapetype
            geojtype = geoj["type"]
            if geojtype == "Null":
                pyshptype = 0
            elif geojtype == "Point":
                pyshptype = 1
            elif geojtype == "LineString":
                pyshptype = 3
            elif geojtype == "Polygon":
                pyshptype = 5
            elif geojtype == "MultiPoint":
                pyshptype = 8
            elif geojtype == "MultiLineString":
                pyshptype = 3
            elif geojtype == "MultiPolygon":
                pyshptype = 5
            shape.shapeType = pyshptype
            
            # set points and parts
            if geojtype == "Point":
                shape.points = [ geoj["coordinates"] ]
                shape.parts = [0]
            elif geojtype in ("MultiPoint","LineString"):
                shape.points = geoj["coordinates"]
                shape.parts = [0]
            elif geojtype in ("Polygon"):
                points = []
                parts = []
                index = 0
                for ext_or_hole in geoj["coordinates"]:
                    points.extend(ext_or_hole)
                    parts.append(index)
                    index += len(ext_or_hole)
                shape.points = points
                shape.parts = parts
            elif geojtype in ("MultiLineString"):
                points = []
                parts = []
                index = 0
                for linestring in geoj["coordinates"]:
                    points.extend(linestring)
                    parts.append(index)
                    index += len(linestring)
                shape.points = points
                shape.parts = parts
            elif geojtype in ("MultiPolygon"):
                points = []
                parts = []
                index = 0
                for polygon in geoj["coordinates"]:
                    for ext_or_hole in polygon:
                        points.extend(ext_or_hole)
                        parts.append(index)
                        index += len(ext_or_hole)
                shape.points = points
                shape.parts = parts
            return shape
        
        # iterate through original shapes
        for row,geom in itertools.izip(rows, geometries):
            shape = geoj2shape(geom)
            shapewriter._shapes.append(shape)
            shapewriter.record(*[encode(value) for value in row])
            
        # save
        shapewriter.save(filepath)

    # geojson file
    elif filepath.endswith((".geojson",".json")):
        geojwriter = pygeoj.new()
        for row,geom in itertools.izip(rows,geometries):
            row = (encode(value) for value in row)
            rowdict = dict(zip(fields, row))
            feat = pygeoj.Feature(properties=rowdict,
                                  geometry=geom)
            geojwriter.addfeature(feat)
        geojwriter.save(filepath)
            
    else:
        raise Exception("Could not save the geometry table to the given filepath: the filetype extension is either missing or not supported")






