

# import builtins
import itertools

# import fileformats
import shapefile as pyshp
import pygeoj



def to_file(fields, rows, geometries, filepath, encoding="utf8", maxprecision=12):

    def encode(value):
        if isinstance(value, int):
            # ints are kept as ints
            return value
        elif isinstance(value, float):
            if value.is_integer():
                return int(value)
            else:
                # floats are rounded
                return round(value, maxprecision)
        elif isinstance(value, unicode):
            # unicode is custom encoded into bytestring
            return value.encode(encoding)
        elif value is None:
            return value
        else:
            # brute force anything else to string representation
            return bytes(value)
    
    # shapefile
    if filepath.endswith(".shp"):
        shapewriter = pyshp.Writer()
        
        # set fields with correct fieldtype
        for fieldindex,fieldname in enumerate(fields):
            fieldlen = 1
            decimals = 0
            fieldtype = "N" # assume number until proven otherwise
            for row in rows:
                value = row[fieldindex]
                if value not in (None,""):
                    try:
                        # make nr fieldtype if content can be made into nr
                        value = float(value)
                        _strnr = format(value, ".%sf"%maxprecision).rstrip(".0")
                        fieldlen = max(( len(_strnr), fieldlen ))
                        if not value.is_integer():
                            # get max decimals, capped to max precision
                            decimals = max(( len(_strnr.split(".")[1]), decimals ))
                    except ValueError:
                        # but turn to text if any of the cells cannot be made to float bc they are txt
                        fieldtype = "C"
                        value = value if isinstance(value, unicode) else bytes(value)
                        fieldlen = max(( len(value), fieldlen ))
                else:
                    # empty value, so just keep assuming same type
                    pass
            # clean fieldname
            fieldname = fieldname.replace(" ","_")[:10]
            # write field
            if fieldtype != "N":
                decimals = 0
            shapewriter.field(fieldname.encode(encoding), fieldtype, fieldlen, decimals)

        # convert geojson to shape
        def geoj2shape(geoj):
            # create empty pyshp shape
            shape = pyshp._Shape()
            # set shapetype
            geojtype = geoj["type"]
            if geojtype == "Null":
                pyshptype = pyshp.NULL
            elif geojtype == "Point":
                pyshptype = pyshp.POINT
            elif geojtype == "LineString":
                pyshptype = pyshp.POLYLINE
            elif geojtype == "Polygon":
                pyshptype = pyshp.POLYGON
            elif geojtype == "MultiPoint":
                pyshptype = pyshp.MULTIPOINT
            elif geojtype == "MultiLineString":
                pyshptype = pyshp.POLYLINE
            elif geojtype == "MultiPolygon":
                pyshptype = pyshp.POLYGON
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
            # encode row values
            row = (encode(value) for value in row)
            rowdict = dict(zip(fields, row))
            # create and add feature
            geojwriter.add_feature(properties=rowdict,
                                   geometry=geom)
        # save
        geojwriter.save(filepath, encoding=encoding)
            
    else:
        raise Exception("Could not save the vector data to the given filepath: the filetype extension is either missing or not supported")






