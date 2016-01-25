
import itertools, operator
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely






# Overlay Analysis (transfer of values, but no clip)

def overlap_summary(groupbydata, valuedata, fieldmapping=[], **kwargs):
    """
    Summarizes the values of "valuedata" that overlap "groupbydata",
    and adds the summary statistics to the output data.

    "fieldmapping" is a list of ('outfieldname', 'getvaluefunction', 'statistic name or function') tuples that decides which
    variables to summarize and how to do so. Valid statistics are count,
    sum, max, min, and average. 
    """

    from . import sql

    out = VectorData()

    # add fields
    out.fields = list(groupbydata.fields)
    out.fields.extend([name for name,valfunc,aggfunc in fieldmapping])

    # loop
    if not hasattr(groupbydata, "spindex"): groupbydata.create_spatial_index()
    if not hasattr(valuedata, "spindex"): valuedata.create_spatial_index()
    for groupfeat in groupbydata.quick_overlap(valuedata.bbox):
        newrow = list(groupfeat.row)
        geom = groupfeat.get_shapely()
        valuefeats = (valfeat for valfeat in valuedata.quick_overlap(groupfeat.bbox))

        # aggregate
        matches = (valfeat for valfeat in valuefeats
                   if valfeat.get_shapely().intersects(geom))
        newrow.extend( sql.aggreg(matches, fieldmapping) )

        # add
        out.add_feature(newrow, geom.__geo_interface__)
        
##    # insert groupby data fields into fieldmapping
##    basefm = [(name,lambda f:f[name],"first") for name in groupbydata.fields]
##    fieldmapping = basefm + fieldmapping
##    out.fields = [name for name,valfunc,aggfunc in fieldmapping]
##
##    # group by each groupby feature
##    iterable = ([(feat,feat.get_shapely()),(otherfeat,otherfeat.get_shapely())]
##                for feat in groupbydata.quick_intersect(valuedata.bbox)
##                for otherfeat in valuedata.quick_intersect(feat.bbox))
##    for group in sql.groupby(iterable, lambda([(f,g),(of,og)]): id(f)):
##
##        # filter to only those that intersect
##        group = sql.where(group, lambda([(f,g),(of,og)]): g.intersects(og))
##
##        # make iter as usually expected by fieldmapping
##        group = ((of,og) for [(f,g),(of,og)] in group)
##
##        # aggregate and add
##        # (not sure if will be correct, in terms of args expected by fieldmapping...?)
##        row,geom = sql.aggreg(group, fieldmapping, lambda(itr): next(itr)[1])
##        out.add_feature(row, geom)

    return out







# Distance Analysis

def near_summary(groupbydata, valuedata,
                 radius=None,   # only those within radius dist
                 fieldmapping=[], 
                 n=None,   # only include n nearest
                 **kwargs):
    """
    Summarizes the values of "valuedata" that are nearest "groupbydata",
    and adds the summary statistics to the output data.

    "fieldmapping" is a list of ('outfieldname', 'getvaluefunction', 'statistic name or function') tuples that decides which
    variables to summarize and how to do so. Valid statistics are count,
    sum, max, min, and average. 
    """

    if not radius and not n:
        raise Exception("Either radius or n (or both) must be set")
    
    # define summary conditions
    # TODO: filters need to optimize using spindex nearest
    # NOTE: also watch out, quick_nearest with limit can lead to wrong results, since not all of those will be within exact distance
    # TODO: instead, always consider all nearest, but instead make efficient algo for stopping
    #       or perhaps multiple expanding quick_nearest...
    # See eg http://www.cs.umd.edu/~hjs/pubs/incnear2.pdf
    # ALSO:
    # speedup by only doing distance calculations once for each unique pair
    # and then looking up to avoid repeat distance calcs

    from . import sql

    out = VectorData()

    # add fields
    out.fields = list(groupbydata.fields)
    out.fields.extend([name for name,valfunc,aggfunc in fieldmapping])

    # loop
    for groupfeat in groupbydata:
        print(groupfeat)
        newrow = list(groupfeat.row)
        geom = groupfeat.get_shapely()

        # precalc all distances (so that iterable is a feat-dist tuple)
        matches = ((valfeat, geom.distance(valfeat.get_shapely())) for valfeat in valuedata)

        # filter to only those within radius
        if radius: 
            matches = sql.where(matches, lambda((f,d)): d <= radius)

        # filter to only n nearest
        if n:
            matches = sorted(matches, key=lambda((f,d)): d)
            matches = sql.limit(matches, n)

        # remove distance from iterable so only feats remain for aggregating
        matches = (f for f,d in matches)

        # aggregate
        newrow.extend( sql.aggreg(matches, fieldmapping) )

        # add
        out.add_feature(newrow, geom.__geo_interface__)

##    # insert groupby data fields into fieldmapping
##    basefm = [(name,lambda f:f[name],"first") for name in groupbydata.fields]
##    fieldmapping = basefm + fieldmapping
##    out.fields = [name for name,valfunc,aggfunc in fieldmapping]
##
##    # group by each groupby feature
##    iterable = ([(feat,feat.get_shapely()),(otherfeat,otherfeat.get_shapely())]
##                for feat in groupbydata for otherfeat in valuedata)
##    for group in sql.groupby(iterable, lambda([(f,g),(of,og)]): id(f)):
##
##        # precalc all distances
##        group = ([(f,g),(of,og),g.distance(og)] for (f,g),(of,og) in group)
##
##        # sort by nearest dist dirst
##        group = sorted(group, key=lambda([(f,g),(of,og),d]): d)
##
##        # filter to only those within radius
##        if radius: 
##            group = sql.where(group, lambda([(f,g),(of,og),d]): d <= radius)
##
##        # filter to only n nearest
##        if n:
##            group = sql.limit(group, n)
##
##        # make iter as usually expected by fieldmapping
##        group = ((of,og) for [(f,g),(of,og),d] in group)
##
##        # aggregate and add
##        # (not sure if will be correct, in terms of args expected by fieldmapping...?)
##        row,geom = sql.aggreg(group, fieldmapping, lambda(itr): next(itr)[1])
##        out.add_feature(row, geom)

    return out

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












