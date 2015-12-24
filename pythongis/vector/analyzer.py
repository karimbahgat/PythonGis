
import itertools, operator
from .data import *

import shapely
from shapely.prepared import prep as supershapely



# Spatial relations summary
# (somewhat lowlevel but provided for advanced and flexible use-cases)

def conditional_summary(groupbydata, valuedata, matchcondition,
                        groupbyfilter=None, valuedatafilter=None,
                        fieldmapping=[], keepall=True, 
                        max_n=None, prepgeom=False):
    # prep
    data1,data2 = groupbydata,valuedata

    if not groupbyfilter: groupbyfilter = lambda: groupbydata
    if not valuedatafilter: valuedatafilter = lambda: valuedata

    def get_aggfunc(agg):
        if agg == "count": return len
        elif agg == "sum": return sum
        elif agg == "max": return max
        elif agg == "min": return min
        elif agg == "average": return lambda seq: sum(seq)/float(len(seq))
        else:
            # agg is not a string, and is assumed already a function
            return agg

    if fieldmapping:
        fieldmapping = [(aggfield,aggtype,get_aggfunc(aggtype)) for aggfield,aggtype in fieldmapping]
        aggfields,aggtypes,aggfuncs = zip(*fieldmapping)

    # create spatial index
    if not hasattr(data1, "spindex"): data1.create_spatial_index()
    if not hasattr(data2, "spindex"): data2.create_spatial_index()

    # create new
    new = VectorData()
    new.fields = list(data1.fields)
    if fieldmapping: 
        for aggfield,aggtype,aggfunc in fieldmapping:
            new.fields.append(aggfield)

    # for each groupby feature
    for i,feat in enumerate(groupbyfilter(data1, data2)):
        geom = feat.get_shapely()
        if prepgeom: # default is False, because limits operations in matchcondition to intersects method, nothing else
            geom = supershapely(geom)
        matches = []

        # get all value features that intersect
        n = 0
        for otherfeat in valuedatafilter(data2, feat): 
            othergeom = otherfeat.get_shapely()
            if matchcondition(geom, othergeom):
                matches.append(otherfeat)
                n += 1
            if max_n and n >= max_n:
                break

        # make newrow from original row
        newrow = list(feat.row)

        # if any matches
        if matches:
            def make_number(value):
                try: return float(value)
                except: return None
                
            # add summary values to newrow based on fieldmapping
            for aggfield,aggtype,aggfunc in fieldmapping:
                values = [otherfeat[aggfield] for otherfeat in matches]
                if aggtype in ("sum","max","min","average"):
                    # only consider number values if numeric stats
                    values = [make_number(value) for value in values if make_number(value) != None]
                if values:
                    summaryvalue = aggfunc(values)
                    ###print "match", aggfunc, values, summaryvalue
                    newrow.append(summaryvalue)
                else:
                    newrow.append("")

        # otherwise, add empty values
        elif keepall:
            ###print "no match"
            newrow.extend(("" for _ in fieldmapping))

        # write feature to output
        new.add_feature(newrow, feat.geometry)

    return new




# Overlay Analysis (transfer of values, but no clip)

def overlap_summary(groupbydata, valuedata, fieldmapping=[], **kwargs):
    """
    Summarizes the values of "valuedata" that overlap "groupbydata",
    and adds the summary statistics to the output data.

    "fieldmapping" is a list of ('fieldname', 'statistic') tuples that decides which
    variables to summarize and how to do so. Valid statistics are count,
    sum, max, min, and average. 
    """
    # define summary conditions
    def _groupbyfilter(groupbydata, valuedata):
        return groupbydata.quick_overlap(valuedata.bbox)

    def _valuedatafilter(valuedata, groupfeat):
        return valuedata.quick_overlap(groupfeat.bbox)
    
    def _matchcondition(geom, othergeom):
        return geom.intersects(othergeom)

    # run
    summarized = conditional_summary(groupbydata, valuedata,
                                     matchcondition=_matchcondition,
                                     groupbyfilter=_groupbyfilter,
                                     valuedatafilter=_valuedatafilter,
                                     fieldmapping=fieldmapping,
                                     prepgeom=True,
                                     **kwargs)

    return summarized




# Distance Analysis

def near_summary(groupbydata, valuedata,
                 radius=None,   # only those within radius dist
                 fieldmapping=[], 
                 n=None,   # only include n nearest
                 **kwargs): 

    if not radius and not n:
        raise Exception("Either radius or n (or both) must be set")
    
    # define summary conditions
    # TODO: filters need to optimize using spindex nearest
    # NOTE: also watch out, quick_nearest with limit can lead to wrong results, since not all of those will be within exact distance
    # TODO: instead, always consider all nearest, but instead make efficient algo for stopping
    #       or perhaps multiple expanding quick_nearest...
    def _groupbyfilter(groupbydata, valuedata):
        return groupbydata

    def _valuedatafilter(valuedata, groupfeat):
        return valuedata.quick_nearest(groupfeat.bbox) if n else valuedata
    
    def _matchcondition(geom, othergeom):
        return geom.distance(othergeom) <= radius if radius else True

    # run
    if n: kwargs["max_n"] = n
    
    summarized = conditional_summary(groupbydata, valuedata,
                                     matchcondition=_matchcondition,
                                     groupbyfilter=_groupbyfilter,
                                     valuedatafilter=_valuedatafilter,
                                     fieldmapping=fieldmapping,
                                     **kwargs)

    return summarized

def nearest_identity(groupbydata, valuedata,
                     radius=None,   # only those within radius dist
                     nearestidfield=None, keepfields=[]):
    # specialized for only the one nearest match
    # recording its distance, and optionally its id, and other attribute fields
    # ...
    pass





# Path Analysis

def travelling_salesman(points, **options):
    pass











# ------------------------
# Move below to the manager.py module
# ........................



# Cut-Glue operations

def glue():
    # aka dissolve
    # aggregate/glue together features in a single layer with same values
    pass

def cut():
    # aka clip
    # clip/cut apart a layer by another layer
    pass






# Select extract operations

def crop():
    # aka intersects(), aka select()
    # keeps only those that intersect with other layer
    # similar to intersection() except doesnt alter any geometries
    pass




# Geometrics

def intersection(*datas):
    pass

def union(*datas):
    pass

def unique(*datas):
    """Those parts of the geometries that are unique(nonintersecting) for each layer"""
    pass

def buffer(data, dist_expression):
    """
    Buffering the data by a positive distance grows the geometry,
    while a negative distance shrinks it. Distance units should be given in
    units of the data's coordinate reference system. 

    Distance is an expression written in Python syntax, where it is possible
    to access the attributes of each feature by writing: feat['fieldname'].
    """
    # buffer and change each geojson dict in-place
    new = VectorData()
    new.fields = list(data.fields)
    for feat in data:
        geom = feat.get_shapely()
        dist = eval(dist_expression)
        buffered = geom.buffer(dist)
        if not buffered.is_empty:
            geojson = buffered.__geo_interface__
            geojson["type"] = buffered.type
            new.add_feature(feat.row, geojson)
    # change data type to polygon
    new.type = "Polygon"
    return new


