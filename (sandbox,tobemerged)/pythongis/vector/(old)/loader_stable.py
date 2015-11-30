
from . import fileformats
from fileformats import shapefile as pyshp
from fileformats import pygeoj
from fileformats import gpxpy


import itertools
def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)


def from_file(filepath):
    
    # shapefile
    if filepath.endswith(".shp"):
        shapereader = pyshp.Reader(filepath)
        fields = [fieldinfo[0] for fieldinfo in shapereader.fields[1:]]
        rows = [ [eachcell for eachcell in eachrecord] for eachrecord in shapereader.iterRecords()]
        geometries = [shape.__geo_interface__ for shape in shapereader.iterShapes()]    
        return fields, rows, geometries

    # geojson file
    elif filepath.endswith(".geojson"):
        geojfile = pygeoj.load(filepath)
        fields = geojfile.common_attributes
        rows = [[feat.properties[field] for field in fields] for feat in geojfile]
        geometries = [feat.geometry for feat in geojfile]
        return fields, rows, geometries

    # kml file
    elif filepath.endswith(".kml"):
        pass

    # wkt file
    elif filepath.endswith(".wkt"):
        pass
    
    # gps data files
    elif filepath.endswith(".gpx"):
        gpx_raw = open(filepath, 'r').read()
        gpxreader = gpxpy.parse(gpx_raw)
    
        fields = ["name","elevation","time","comment","speed"]
        _pointpairs = pairwise(( point
                      for track in gpxreader.tracks
                      for segment in track.segments
                      for point in segment.points))

        # maybe also store route and waypoint info...
        # ...

        rowgeoms = []
        for pointpair in _pointpairs:
            start,stop = pointpair
            rowgeoms.append(((start.name,start.elevation,start.time,start.comment,start.speed),
                     {"type":"LineString",
                       "coordinates":((start.latitude,start.longitude),
                                      (stop.latitude,stop.longitude)) }))
        if not rowgeoms: raise Exception("No tracks to retrieve")
        rows,geometries = itertools.izip(*rowgeoms)
        return fields, rows, geometries

    else:
        raise TypeError("Could not create a geometry table from the given filepath: the filetype extension is either missing or not supported")






