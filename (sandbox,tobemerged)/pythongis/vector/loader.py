
import os

from . import fileformats
from fileformats import shapefile as pyshp
from fileformats import pygeoj
from fileformats import gpxpy


import itertools
def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)



def from_file(filepath, encoding="utf8"):

    def decode(value):
        if isinstance(value, str): 
            return value.decode(encoding)
        else: return value
    
    # shapefile
    if filepath.endswith(".shp"):
        shapereader = pyshp.Reader(filepath)
        fields = [decode(fieldinfo[0]) for fieldinfo in shapereader.fields[1:]]
        rows = [ [decode(value) for value in record] for record in shapereader.iterRecords()]
        def getgeoj(obj):
            geoj = obj.__geo_interface__
            if hasattr(obj, "bbox"): geoj["bbox"] = obj.bbox
            return geoj
        geometries = [getgeoj(shape) for shape in shapereader.iterShapes()]
        if os.path.lexists(filepath[:-4] + ".prj"):
            crs = open(filepath[:-4] + ".prj", "r").read()
        else: crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
        return fields, rows, geometries, crs

    # geojson file
    elif filepath.endswith((".geojson",".json")):
        geojfile = pygeoj.load(filepath)
        fields = [decode(field) for field in geojfile.common_attributes]
        rows = [[decode(feat.properties[field]) for field in fields] for feat in geojfile]
        geometries = [feat.geometry.__geo_interface__ for feat in geojfile]
        crs = geojfile.crs
        return fields, rows, geometries, crs
    
    # gps data files
    elif filepath.endswith(".gpx"):
        gpx_raw = open(filepath, 'r').read()
        gpxreader = gpxpy.parse(gpx_raw)
    
        fields = ["name","elevation","time","comment","speed"]
        rows = []
        geometries = []
        for track in gpxreader.tracks:
            # example: roadtrip 1, roadtrip 2, ...
            for segment in track.segments:
                # example: before signal lost in tunnel, after tunnel, ...
                for pointpair in pairwise(segment.points):
                    start,stop = pointpair
                    row = [decode(value) for value in (start.name,start.elevation,start.time,start.comment,start.speed)]
                    geom = {"type":"LineString",
                            "coordinates":((start.latitude,start.longitude),
                                           (stop.latitude,stop.longitude)) }
                    rows.append(row)
                    geometries.append(geom)

        if not geometries: raise Exception("File not loaded: No GPX tracks to retrieve")
        
        return fields, rows, geometries

    else:
        raise Exception("Could not create a geometry table from the given filepath: the filetype extension is either missing or not supported")






