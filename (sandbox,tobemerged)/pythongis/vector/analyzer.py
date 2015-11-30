
import itertools, operator
from .data import *

import shapely, shapely.ops
from shapely.geometry import asShape as geoj2shapely
from shapely.geometry import mapping as shapely2geoj
from shapely.prepared import prep as supershapely



# Distinction between cut and glue operations
# cut: ...
# glue: ...

# Or how about this:
# spatial link: join attribs, option to use match geometry (ala geoproc)
# spatial glue: dissolve
# spatial cut: difference

# Clipping to region of interest (no transfer of values)
# should belongs in management.py
# maybe rename to crop?
# and allow any nr of datainput, only keeping common to all

def vector_clip_overlap(data, clip):
    pass

def vector_clip_difference(*datalist):
    pass

def vector_clip_symmetrical_difference(*datalist):
    pass



# Clip (with transfer of values)???
# ala Arcgis intersect/union/diff
# essentially same as clipping all layers, then spajoin together results
# so maybe unnecessary?

##def vector_intersect(*datalist):
##    # detect lowest dimension geotype
##    lowestgeotype = "Polygon"
##    for data in datalist:
##        if "LineString" in data.type:
##            lowestgeotype = "LineString"
##        elif "Point" in data.type:
##            lowestgeotype = "Point"
##            break # lowest possible
##    # create spatial index for all data
##    for data in datalist:
##        data.create_spatial_index()
##    # get first data
##    data = datalist[0]
##    # create new
##    new = GeoTable()
##    new.fields = list(data.fields)
##    # intersect each feat in first with all others
##    def process_intersection(intersection):
##        if lowestgeotype in intersection.type:
##            geoj = shapely2geoj(intersection)
##            new.add_feature(feat.row, geoj) 
##    for feat in data:
##        print feat.id
##        geom = geoj2shapely(feat.geometry)
##        for otherfeat in datalist[1].quick_overlap(feat.bbox):
##            othergeom = geoj2shapely(otherfeat.geometry)
##            intersection = geom.intersection(othergeom)
##            if not intersection.is_empty:
##                if intersection.type == "GeometryCollection":
##                    for subintsec in intersection:
##                        process_intersection(subintsec)
##                else:
##                    process_intersection(intersection)
##    return new











# Overlay Analysis (transfer of values, but no clip)

def vector_spatialjoin(data1, data2, joincondition, radius=None):
    """Possible joinconditions:
        intersects, within, contains, crosses, touches, equals
       Also:
        distance
    """
    # create spatial index
    if not hasattr(data1, "spindex"): data1.create_spatial_index()
    if not hasattr(data2, "spindex"): data2.create_spatial_index()
    # create new
    new = GeoTable()
    new.fields = list(data1.fields)
    new.fields.extend(data2.fields)
    # intersect each feat in first with all others
    if joincondition in ("distance",):
        new.fields.append("DISTANCE")
        if joincondition == "distance" and radius is None: raise Exception("radius arg must be set when using distance mode")
        maxnum = 9223372036854775807
        for feat in data1.quick_nearest(data2.bbox, n=maxnum):
            geom = geoj2shapely(feat.geometry)
            matchtest = getattr(geom, "distance")
            for otherfeat in data2.quick_nearest(feat.bbox, n=maxnum):
                othergeom = geoj2shapely(otherfeat.geometry)
                match = matchtest(othergeom)
                if match <= radius:
                    joined = list(feat.row)
                    joined.extend(otherfeat.row)
                    joined.append(match)
                    print "match", match
                    new.add_feature(joined, feat.geometry)
    else:
        for feat in data1.quick_overlap(data2.bbox):
            geom = geoj2shapely(feat.geometry)
            matchtest = getattr(geom, joincondition)
            for otherfeat in data2.quick_overlap(feat.bbox):
                othergeom = geoj2shapely(otherfeat.geometry)
                match = matchtest(othergeom)
                if match:
                    joined = list(feat.row)
                    joined.extend(otherfeat.row)
                    print "match", len(joined)
                    new.add_feature(joined, feat.geometry)

    return new

def overlap_summary(groupbydata, valuedata, fieldmapping=[]):
    # prep
    data1,data2 = groupbydata,valuedata
    if fieldmapping: aggfields,aggtypes = zip(*fieldmapping)
    aggfunctions = dict([("count",len),
                         ("sum",sum),
                         ("max",max),
                         ("min",min),
                         ("average",lambda seq: sum(seq)/float(len(seq)) ) ])

    # create spatial index
    if not hasattr(data1, "spindex"): data1.create_spatial_index()
    if not hasattr(data2, "spindex"): data2.create_spatial_index()

    # create new
    new = GeoTable()
    new.fields = list(data1.fields)
    if fieldmapping: 
        for aggfield,aggtype in fieldmapping:
            new.fields.append(aggfield)

    # for each groupby feature
    for i,feat in enumerate(data1.quick_overlap(data2.bbox)):
        geom = geoj2shapely(feat.geometry)
        geom = supershapely(geom)
        matches = []

        # get all value features that intersect
        for otherfeat in data2.quick_overlap(feat.bbox):        
            othergeom = geoj2shapely(otherfeat.geometry)
            if geom.intersects(othergeom):
                matches.append(otherfeat)

        # make newrow from original row
        newrow = list(feat.row)

        # if any matches
        if matches:
            def make_number(value):
                try: return float(value)
                except: return None
                
            # add summary values to newrow based on fieldmapping
            for aggfield,aggtype in fieldmapping:
                values = [otherfeat[aggfield] for otherfeat in matches]
                if aggtype in ("sum","max","min","average"):
                    # only consider number values if numeric stats
                    values = [make_number(value) for value in values if make_number(value) != None]
                aggregatefunc = aggfunctions[aggtype]
                summaryvalue = aggregatefunc(values)
                newrow.append(summaryvalue)

        # otherwise, add empty values
        else:
            newrow.extend(("" for _ in fieldmapping))

        # write feature to output
        new.add_feature(newrow, feat.geometry)

    return new



# Distance Analysis

def vector_nearest(data, otherdata, search_radius=None, n=1):
    pass

def vector_buffer(data, dist_expression):
    # buffer and change each geojson dict in-place
    new = GeoTable()
    new.fields = list(data.fields)
    for feat in data:
        geom = geoj2shapely(feat.geometry)
        dist = eval(dist_expression)
        buffered = geom.buffer(dist)
        if not buffered.is_empty:
            geoj = shapely2geoj(buffered)
            geoj["type"] = buffered.type
            new.add_feature(feat.row, geoj)
    # change data type to polygon
    new.type = "Polygon"
    return new





