
import itertools, operator
from .data import *

import shapely, shapely.ops
from shapely.geometry import asShape as geoj2shapely
from shapely.geometry import mapping as shapely2geoj

#from .._thirdparty import pytesselate as pytess

# File management

def vector_crop(data, cropby):
    #cropby is another data instance
    #essentially same as selectbylocation
    pass

def vector_split(data, splitfields):
    fieldindexes = [index for index,field in enumerate(data.fields)
                    if field in splitfields]
    sortedfeatures = sorted(data, key=operator.itemgetter(*fieldindexes))
    grouped = itertools.groupby(sortedfeatures, key=operator.itemgetter(*fieldindexes))
    for splitid,features in grouped:
        outfile = GeoTable()
        outfile.fields = list(data.fields)
        for oldfeat in features:
            outfile.add_feature(oldfeat.row, oldfeat.geometry)
        yield outfile

def vector_merge(*datalist):
    #make empty table
    firstfile = datalist[0]
    outfile = GeoTable()
    #combine fields from all files
    outfields = list(firstfile.fields)
    for data in datalist[1:]:
        for field in data.fields:
            if field not in outfields:
                outfields.append(field)
    outfile.fields = outfields
    #add the rest of the files
    for data in datalist:
        for feature in data:
            geometry = feature.geometry.copy()
            row = []
            for field in outfile.fields:
                if field in data.fields:
                    row.append( feature[field] )
                else:
                    row.append( "" )
            outfile.add_feature(row, geometry)
    #return merged file
    return outfile


# Polishing

def vector_clean(data, tolerance=0):
    """Cleans the vector data of unnecessary clutter such as repeat
    points or closely related points within the distance specified in the
    'tolerance' parameter. Also tries to fix any broken geometries, dropping
    any unfixable ones.

    Adds the resulting cleaned data to the layers list.
    """
    # create new file
    outfile = GeoTable()
    outfile.fields = list(data.fields)

    # clean
    for feat in data:
        shapelyobj = geoj2shapely(feat.geometry)
        
        # try fixing invalid geoms
        if not shapelyobj.is_valid:
            if "Polygon" in shapelyobj.type:
                # fix bowtie polygons
                shapelyobj = shapelyobj.buffer(0.0)

        # remove repeat points (tolerance=0)
        # (and optionally smooth out complex shapes, tolerance >= 1)
        shapelyobj = shapelyobj.simplify(tolerance)
            
        # if still invalid, do not add to output
        if not shapelyobj.is_valid:
            continue

        # write to file
        geoj = shapely2geoj(shapelyobj)
        outfile.add_feature(feat.row, geoj)

    return outfile





# Converting between geometry types

def _to_multicentroids(data):
    """create multiple centroid points for each multi geometry part"""
    
    # create new file
    outfile = GeoTable()
    outfile.fields = list(data.fields)
    
    # loop features
    if "LineString" in data.type or "Polygon" in data.type:
        for feat in data:
            if "Multi" in feat.geometry["type"]:
                multishape = geoj2shapely(feat.geometry)
                for geom in multishape.geoms:
                    shapelypoint = geom.centroid
                    geoj = shapely2geoj(shapelypoint)
                    outfile.add_feature(feat.row, geoj)
            else:
                shapelypoint = geoj2shapely(feat.geometry).centroid
                geoj = shapely2geoj(shapelypoint)
                outfile.add_feature(feat.row, geoj)
        return outfile
    
    else:
        return data.copy()

def _to_centroids(data):
    """create one centroid point for each multi geometry part"""
    
    # create new file
    outfile = GeoTable()
    outfile.fields = list(data.fields)
    
    # loop features
    for feat in data:
        if feat.geometry["type"] != "Point":
            shapelypoint = geoj2shapely(feat.geometry).centroid
            geoj = shapely2geoj(shapelypoint)
            outfile.add_feature(feat.row, geoj)
    return outfile

def _to_vertexes(data):
    """create points at every vertex, incl holes"""
    
    # create new file
    outfile = GeoTable()
    outfile.fields = list(data.fields)
    
    # loop points
    if "LineString" in data.type:
        for feat in data:
            if "Multi" in feat.geometry["type"]:
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
            if "Multi" in feat.geometry["type"]:
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

def vector_to_points(data, pointtype="vertex"):
    if pointtype == "vertex":
        return _to_vertexes(data)
    
    elif pointtype == "centroid":
        return _to_centroids(data)
    
    elif pointtype == "multicentroid":
        return _to_multicentroids(data)

def vector_to_lines(data, linetype=""):
    if "Point" in data.type:
        # create new file
        outfile = GeoTable()
        outfile.fields = list(data.fields)

        # connect all points in the data into a single long line in the order that they are found
        linecoords = []
        for feat in data:
            geotype = feat.geometry["type"]
            if "Multi" in geotype:
                points = feat.geometry["coordinates"]
                linecoords.extend(points)
            else:
                point = feat.geometry["coordinates"]
                linecoords.append(point)
        geoj = {"type": "LineString",
                "coordinates": linecoords} 
        outfile.add_feature([], geoj)
        return outfile

    elif "Polygon" in data.type:
        # create new file
        outfile = GeoTable()
        outfile.fields = list(data.fields)
    
        # take only exterior polygon and change type to linestring
        for feat in data:
            if "Multi" in feat.geometry["type"]:
                for polygon in feat.geometry["coordinates"]:
                    # delete last point to not make it a closed ring
                    polygon = polygon[0] #[ext_or_holes[:-1] for ext_or_holes in polygon]
                    # add feature
                    geoj = {"type": "LineString",
                            "coordinates": polygon} 
                    outfile.add_feature(feat.row, geoj)
            else:
                polygon = feat.geometry["coordinates"]
                # delete last point to not make it a closed ring
                polygon = polygon[0] #[ext_or_holes[:-1] for ext_or_holes in polygon]
                # add feature
                geoj = {"type": "LineString",
                        "coordinates": polygon}
                outfile.add_feature(feat.row, geoj)
        return outfile
    
    else:
        return data.copy()

def vector_to_polygons(data, polytype="convex hull"):
    # create new file
    outfile = GeoTable()
    outfile.fields = list(data.fields)
        
    if polytype == "convex hull":
        for feat in data:
            shapelygeom = geoj2shapely(feat.geometry)
            convex = shapelygeom.convex_hull
            geoj = shapely2geoj(convex)
            # sometimes the convex hull is only a line or point
            # but we cannot mix shapetypes, so exclude those
            if geoj["type"] == "Polygon":
                outfile.add_feature(feat.row, geoj)
            
        return outfile

    elif polytype == "delauney triangles":
        if "Point" in data.type:
            def get_flattened_points():
                for feat in data:
                    if "Multi" in feat.geometry["type"]:
                        for point in feat.geometry["coordinates"]:
                            yield point
                    else: yield feat.geometry["coordinates"]
            triangles = pytess.triangulate(get_flattened_points())
            # triangle polygons are between multiple existing points,
            # so do not inherit any attributes
            for tri in triangles:
                geoj = {"type": "Polygon",
                        "coordinates": [tri] }
                row = ["" for field in outfile.fields]
                outfile.add_feature(row, geoj)

            return outfile

        else:
            raise Exception("Delauney triangles can only be made from point data")

    elif polytype == "voronoi polygons":
        if "Point" in data.type:
            def get_flattened_points():
                for feat in data:
                    if "Multi" in feat.geometry["type"]:
                        for point in feat.geometry["coordinates"]:
                            yield point
                    else: yield feat.geometry["coordinates"]
            results = pytess.voronoi(get_flattened_points())
            # return new file with polygon geometries
            for midpoint,polygon in results:
                geoj = {"type": "Polygon",
                        "coordinates": [polygon] }
                row = ["" for field in outfile.fields]
                outfile.add_feature(row, geoj)

            return outfile

        else:
            raise Exception("Voronoi polygons can only be made from point data")

    elif polytype == "enclose lines":
        if "LineString" in data.type:
            shapelylines = (geoj2shapely(feat.geometry) for feat in data)
            for polygon in shapely.ops.polygonize(shapelylines):
                geoj = shapely2geoj(polygon)
                row = ["" for field in outfile.fields]
                outfile.add_feature(row, geoj)

            return outfile
        
        else:
            raise Exception("Enclose lines can only be done on line data")


def vector_flatten_multiparts(data):
    # force all multi-geometries to be decoupled into several singlegeoms with same properties
    pass

def vector_group_singleparts(data, groupfield):
    # group single-geometries based on unique groupfield
    pass



# Create new geometries

##def _great_circle_path(point1, point2, segments):
##    # http://gis.stackexchange.com/questions/47/what-tools-in-python-are-available-for-doing-great-circle-distance-line-creati
##    ptlon1,ptlat1 = point1
##    ptlon2,ptlat2 = point2
##
##    numberofsegments = segments
##    onelessthansegments = numberofsegments - 1
##    fractionalincrement = (1.0/onelessthansegments)
##
##    ptlon1_radians = math.radians(ptlon1)
##    ptlat1_radians = math.radians(ptlat1)
##    ptlon2_radians = math.radians(ptlon2)
##    ptlat2_radians = math.radians(ptlat2)
##
##    distance_radians=2*math.asin(math.sqrt(math.pow((math.sin((ptlat1_radians-ptlat2_radians)/2)),2) + math.cos(ptlat1_radians)*math.cos(ptlat2_radians)*math.pow((math.sin((ptlon1_radians-ptlon2_radians)/2)),2)))
##    # 6371.009 represents the mean radius of the earth
##    # shortest path distance
##    distance_km = 6371.009 * distance_radians
##
##    mylats = []
##    mylons = []
##
##    # write the starting coordinates
##    mylats.append([])
##    mylons.append([])
##    mylats[0] = ptlat1
##    mylons[0] = ptlon1 
##
##    f = fractionalincrement
##    icounter = 1
##    while icounter < onelessthansegments:
##        icountmin1 = icounter - 1
##        mylats.append([])
##        mylons.append([])
##        # f is expressed as a fraction along the route from point 1 to point 2
##        A=math.sin((1-f)*distance_radians)/math.sin(distance_radians)
##        B=math.sin(f*distance_radians)/math.sin(distance_radians)
##        x = A*math.cos(ptlat1_radians)*math.cos(ptlon1_radians) + B*math.cos(ptlat2_radians)*math.cos(ptlon2_radians)
##        y = A*math.cos(ptlat1_radians)*math.sin(ptlon1_radians) +  B*math.cos(ptlat2_radians)*math.sin(ptlon2_radians)
##        z = A*math.sin(ptlat1_radians) + B*math.sin(ptlat2_radians)
##        newlat=math.atan2(z,math.sqrt(math.pow(x,2)+math.pow(y,2)))
##        newlon=math.atan2(y,x)
##        newlat_degrees = math.degrees(newlat)
##        newlon_degrees = math.degrees(newlon)
##        mylats[icounter] = newlat_degrees
##        mylons[icounter] = newlon_degrees
##        icounter += 1
##        f = f + fractionalincrement
##
##    # write the ending coordinates
##    mylats.append([])
##    mylons.append([])
##    mylats[onelessthansegments] = ptlat2
##    mylons[onelessthansegments] = ptlon2
##
##def vector_point_pairs_to_great_circles(frompoints, topoints, connectcriteria):
##    # 1: either a table, drawing between from/to coordinate fields
##    # ...
##    
##    # 2: or two point files, and for each frompoint draw line to each topoint
##    # ...that satisfies a criteria function. store the id of the from and topoint
##    # ...as fields.
##    def flatten(data):
##        for feat in data:
##            geotype = feat.geometry["type"]
##            coords = feat.geometry["coordinates"]
##            if "Multi" in geotype:
##                for singlepart in coords:
##                    geoj = {"type": geotype.replace("Multi", ""),
##                            "coordinates": singlepart}
##                    yield feat.id, feat.row, geoj
##            else:
##                yield feat.id, feat.row, feat.geometry
##
##    # create new file
##    outfile = GeoTable()
##    outfile.fields = ["fromid", "toid"]
##
##    # connect points matching criteria
##    for fromid,fromrow,frompoint in flatten(frompoints):
##        for toid,torow,topoint in flatten(topoints):
##            match = connectcriteria(fromrow, torow)
##            if match:
##                linepath = _great_circle_path(frompoint, topoint, segments=100)
##                geoj = {"type": "LineString",
##                        "coordinates": linepath}
##                row = [fromid, toidf]
##                outfile.add_feature(row, geoj)
##
##    return outfile
                



# Editing vertices

def vector_add_point(data, point, position):
    pass

def vector_move_point(data, point, position):
    pass

def vector_insert_point(data, point, position):
    pass

def vector_delete_point(data, point, position):
    pass






