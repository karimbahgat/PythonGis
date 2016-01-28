
# import builtins
import os

# import fileformat modules
import shapefile as pyshp
import pygeoj


def from_file(filepath, encoding="utf8", **kwargs):

    def decode(value):
        if isinstance(value, str): 
            return value.decode(encoding)
        else: return value
    
    # shapefile
    if filepath.endswith(".shp"):
        shapereader = pyshp.Reader(filepath, **kwargs) # TODO: does pyshp take kwargs?
        
        # load fields, rows, and geometries
        fields = [decode(fieldinfo[0]) for fieldinfo in shapereader.fields[1:]]
        rows = [ [decode(value) for value in record] for record in shapereader.iterRecords()]
        def getgeoj(obj):
            geoj = obj.__geo_interface__
            if hasattr(obj, "bbox"): geoj["bbox"] = list(obj.bbox)
            return geoj
        geometries = [getgeoj(shape) for shape in shapereader.iterShapes()]
        
        # load projection string from .prj file if exists
        if os.path.lexists(filepath[:-4] + ".prj"):
            crs = open(filepath[:-4] + ".prj", "r").read()
        else: crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
        
        return fields, rows, geometries, crs

    # geojson file
    elif filepath.endswith((".geojson",".json")):
        geojfile = pygeoj.load(filepath, encoding=encoding, **kwargs)

        # load fields, rows, and geometries
        fields = [field for field in geojfile.common_attributes]
        rows = [[feat.properties[field] for field in fields] for feat in geojfile]
        geometries = [feat.geometry.__geo_interface__ for feat in geojfile]

        # load crs
        crs = geojfile.crs
        
        return fields, rows, geometries, crs
    
    else:
        raise Exception("Could not create vector data from the given filepath: the filetype extension is either missing or not supported")






