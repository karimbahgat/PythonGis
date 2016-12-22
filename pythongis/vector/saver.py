

# import builtins
import itertools

# import fileformats
import shapefile as pyshp
import pygeoj



def to_file(fields, rows, geometries, filepath, encoding="utf8", maxprecision=12, **kwargs):

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

    def detect_fieldtypes(fields, rows):
        # TODO: allow other data types such as dates etc...
        # set fields with correct fieldtype
        fieldtypes = []
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
                        if value.is_integer():
                            _strnr = bytes(value)
                        else:
                            # get max decimals, capped to max precision
                            _strnr = format(value, ".%sf"%maxprecision).rstrip("0")
                            decimals = max(( len(_strnr.split(".")[1]), decimals ))
                        fieldlen = max(( len(_strnr), fieldlen ))
                    except ValueError:
                        # but turn to text if any of the cells cannot be made to float bc they are txt
                        fieldtype = "C"
                        value = value if isinstance(value, unicode) else bytes(value)
                        fieldlen = max(( len(value), fieldlen ))
                else:
                    # empty value, so just keep assuming same type
                    pass
            if fieldtype == "N" and decimals == 0:
                fieldlen -= 2 # bc above we measure lengths for ints as if they were floats, ie with an additional ".0"
                func = lambda v: "" if v in (None,"") else int(v)
            elif fieldtype == "N" and decimals:
                func = lambda v: "" if v in (None,"") else float(v)
            elif fieldtype == "C":
                func = lambda v: v #encoding are handled later
            else:
                raise Exception("Unexpected bug: Detected field should be always N or C")
            fieldtypes.append( (fieldtype,func,fieldlen,decimals) )
        return fieldtypes
    
    # shapefile
    if filepath.endswith(".shp"):
        shapewriter = pyshp.Writer()

        fieldtypes = detect_fieldtypes(fields,rows)
        
        # set fields with correct fieldtype
        for fieldname,(fieldtype,func,fieldlen,decimals) in itertools.izip(fields, fieldtypes):
            fieldname = fieldname.replace(" ","_")[:10]
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
            row = [encode(func(value)) for (typ,func,length,deci),value in zip(fieldtypes,row)]
            shapewriter.record(*row)
            
        # save
        shapewriter.save(filepath)

    # geojson file
    elif filepath.endswith((".geojson",".json")):
        geojwriter = pygeoj.new()
        fieldtypes = detect_fieldtypes(fields,rows)
        for row,geom in itertools.izip(rows,geometries):
            # encode row values
            row = (func(value) for (typ,func,length,deci),value in zip(fieldtypes,row))
            row = (encode(value) for value in row)
            rowdict = dict(zip(fields, row))
            # create and add feature
            geojwriter.add_feature(properties=rowdict,
                                   geometry=geom)
        # save
        geojwriter.save(filepath, encoding=encoding)

    # normal table file without geometry
    elif filepath.endswith((".txt",".csv")):
        import csv
        
        # TODO: Add option of saving geoms as strings in separate fields
        with open(filepath, "wb") as fileobj:
            csvopts = dict()
            csvopts["delimiter"] = kwargs.get("delimiter", ";") # tab is best for automatically opening in excel...
            writer = csv.writer(fileobj, **csvopts)
            writer.writerow([f.encode(encoding) for f in fields])
            for row,geometry in itertools.izip(rows, geometries):
                writer.writerow([encode(val) for val in row])

    elif filepath.endswith(".xls"):
        import xlwt
        
        with open(filepath, "wb") as fileobj:
            wb = xlwt.Workbook(encoding=encoding) # module takes care of encoding for us
            sheet = wb.add_sheet("Data")
            # fields
            for c,f in enumerate(fields):
                sheet.write(0, c, f)
            # rows
            for r,(row,geometry) in enumerate(itertools.izip(rows, geometries)):
                for c,val in enumerate(row):
                    # TODO: run val through encode() func, must spit out dates as well
                    sheet.write(r+1, c, val)
            # save
            wb.save(filepath)
            
    else:
        raise Exception("Could not save the vector data to the given filepath: the filetype extension is either missing or not supported")






