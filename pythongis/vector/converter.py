"""
Module for converting the geometry type of vector datasets, 
e.g. converting a polygon or linestring dataset to a point dataset. 

TODO:
- Add "to_linestring", and "to_polygon" functions. 
"""

import itertools, operator, math
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely



# Common helper functions 

def _to_multicentroids(data):
    """create multiple centroid points for each multi geometry part"""
    
    # create new file
    outfile = VectorData()
    outfile.fields = list(data.fields)
    
    # loop features
    if "LineString" in data.type or "Polygon" in data.type:
        for feat in data:
            if not feat.geometry:
                outfile.add_feature(feat.row, None)
            elif "Multi" in feat.geometry["type"]:
                multishape = feat.get_shapely()
                for geom in multishape.geoms:
                    shapelypoint = geom.centroid
                    geoj = shapelypoint.__geo_interface__
                    outfile.add_feature(feat.row, geoj)
            else:
                shapelypoint = feat.get_shapely().centroid
                geoj = shapelypoint.__geo_interface__
                outfile.add_feature(feat.row, geoj)
        return outfile
    
    else:
        return data.copy()

def _to_centroids(data):
    """create one centroid point for each multi geometry part"""
    
    # create new file
    outfile = VectorData()
    outfile.fields = list(data.fields)
    
    # loop features
    for feat in data:
        if not feat.geometry:
            outfile.add_feature(feat.row, None)
        elif feat.geometry["type"] != "Point":
            shapelypoint = feat.get_shapely().centroid
            geoj = shapelypoint.__geo_interface__
            outfile.add_feature(feat.row, geoj)
    return outfile

def _to_vertexes(data):
    """create points at every vertex, incl holes"""
    
    # create new file
    outfile = VectorData()
    outfile.fields = list(data.fields)
    
    # loop points
    if "LineString" in data.type:
        for feat in data:
            if not feat.geometry:
                outfile.add_feature(feat.row, None)
            elif "Multi" in feat.geometry["type"]:
                for linestring in feat.geometry["coordinates"]:
                    for point in linsetring:
                        geoj = {"type": "Point",
                                "coordinates": point}
                        outfile.add_feature(feat.row, geoj)
            else:
                for point in feat.geometry["coordinates"]:
                    geoj = {"type": "Point",
                            "coordinates": point}
                    outfile.add_feature(feat.row, geoj)
        return outfile
                        
    elif "Polygon" in data.type:
        for feat in data:
            if not feat.geometry:
                outfile.add_feature(feat.row, None)
            elif "Multi" in feat.geometry["type"]:
                for polygon in feat.geometry["coordinates"]:
                    for ext_or_hole in polygon:
                        for point in ext_or_hole:
                            geoj = {"type": "Point",
                                    "coordinates": point}
                            outfile.add_feature(feat.row, geoj)
            else:
                for ext_or_hole in feat.geometry["coordinates"]:
                    for point in ext_or_hole:
                        geoj = {"type": "Point",
                                "coordinates": point}
                        outfile.add_feature(feat.row, geoj)
        return outfile
    
    else:
        return data.copy()




# Converting between geometry types

def to_points(data, pointtype="centroid"):
    """
    Converts every feature in a non-point vector dataset to one or more point features, returning a new instance. 
    Pointtype can be centroid (default), multicentroid (one for each multipart), or vertex (a point at every vertex). 
    """
    if pointtype == "vertex":
        return _to_vertexes(data)
    
    elif pointtype == "centroid":
        return _to_centroids(data)
    
    elif pointtype == "multicentroid":
        return _to_multicentroids(data)


