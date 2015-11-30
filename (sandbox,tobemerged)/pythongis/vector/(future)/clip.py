
from shapely import ops

def intersect(geotable1, geotable2):
    resultgeoms = []

    if hasattr(geotable1, "spindex"):
        geotable1_features = geotable1.quick_overlap(geotable2.bbox)
    else: geotable1_features = geotable1.features

    if hasattr(geotable2, "spindex"):
        geotable2_features = geotable2.quick_overlap(geotable1.bbox)
    else: geotable1_features = geotable1.features
        
    for feat1 in geotable1_features:
        for feat2 in geotable2_features:
            _geom = feat1.geometry.intersect(feat2.geometry)
            if _geom: resultgeoms.append((feat1,feat2,_geom))
            
    new = GeoTable()
    new.fields = list(set(geotable1.fields).intersect(geotable2.fields))
    # then transfer the row values...?
    return new


def union(geotable1, geotable2):
    resultgeoms = []

    # actually use ops.cascaded_union instead...

    for feat1 in geotable1:
        for feat2 in geotable2:
            _geom = feat1.geometry.union(feat2.geometry)
            if _geom: resultgeoms.append((feat1,feat2,_geom))
            
    new = GeoTable()
    new.fields = list(set(geotable1.fields).intersect(geotable2.fields))
    # then transfer the row values...?
    return new
        
