
import itertools, operator
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely



# TODO: REDO OVERLAP AND NEAREST SUMMARY USING SQL FUNCS
        
### Spatial relations summary
### (somewhat lowlevel but provided for advanced and flexible use-cases)
##
##def conditional_summary(groupbydata, valuedata, matchcondition,
##                        groupbyfilter=None, valuedatafilter=None,
##                        fieldmapping=[], keepall=True, 
##                        max_n=None, prepgeom=False):
##    
##    data1,data2 = groupbydata,valuedata
##
##    # if no filter, main data is always first arg so return first item unfiltered
##    if not groupbyfilter: groupbyfilter = lambda gd,vd: gd
##    if not valuedatafilter: valuedatafilter = lambda vd,gf: vd
##
##    def get_aggfunc(agg):
##        if agg == "count": return len
##        elif agg == "sum": return sum
##        elif agg == "max": return max
##        elif agg == "min": return min
##        elif agg == "average": return lambda seq: sum(seq)/float(len(seq))
##        else:
##            # agg is not a string, and is assumed already a function
##            return agg
##
##    if fieldmapping:
##        fieldmapping = [(aggfield,aggtype,get_aggfunc(aggtype)) for aggfield,aggtype in fieldmapping]
##        aggfields,aggtypes,aggfuncs = zip(*fieldmapping)
##
##    # create spatial index
##    if not hasattr(data1, "spindex"): data1.create_spatial_index()
##    if not hasattr(data2, "spindex"): data2.create_spatial_index()
##
##    # create new
##    new = VectorData()
##    new.fields = list(data1.fields)
##    if fieldmapping: 
##        for aggfield,aggtype,aggfunc in fieldmapping:
##            new.fields.append(aggfield)
##
##    # for each groupby feature
##    for i,feat in enumerate(groupbyfilter(data1, data2)):
##        geom = feat.get_shapely()
##        if prepgeom: # default is False, because limits operations in matchcondition to intersects method, nothing else
##            geom = supershapely(geom)
##        matches = []
##
##        # get all value features that match a condition
##        n = 0
##        for otherfeat in valuedatafilter(data2, feat): 
##            othergeom = otherfeat.get_shapely()
##            if matchcondition(feat, geom, otherfeat, othergeom):
##                matches.append(otherfeat)
##                n += 1
##            if max_n and n >= max_n:
##                break
##
##        # make newrow from original row
##        newrow = list(feat.row)
##
##        # if any matches
##        if matches:
##            def make_number(value):
##                try: return float(value)
##                except: return None
##                
##            # add summary values to newrow based on fieldmapping
##            for aggfield,aggtype,aggfunc in fieldmapping:
##                values = [otherfeat[aggfield] for otherfeat in matches]
##                if aggtype in ("sum","max","min","average"):
##                    # only consider number values if numeric stats
##                    values = [make_number(value) for value in values if make_number(value) != None]
##                if values:
##                    summaryvalue = aggfunc(values)
##                    ###print "match", aggfunc, values, summaryvalue
##                    newrow.append(summaryvalue)
##                else:
##                    newrow.append("")
##
##        # otherwise, add empty values
##        elif keepall:
##            ###print "no match"
##            newrow.extend(("" for _ in fieldmapping))
##
##        # write feature to output
##        new.add_feature(newrow, feat.geometry)
##
##    return new






# Overlay Analysis (transfer of values, but no clip)

def overlap_summary(groupbydata, valuedata, fieldmapping=[], **kwargs):
    """
    Summarizes the values of "valuedata" that overlap "groupbydata",
    and adds the summary statistics to the output data.

    "fieldmapping" is a list of ('fieldname', 'statistic') tuples that decides which
    variables to summarize and how to do so. Valid statistics are count,
    sum, max, min, and average. 
    """

    raise Exception("Refurbishing...")
    
##    # define summary conditions
##    def _groupbyfilter(groupbydata, valuedata):
##        return groupbydata.quick_overlap(valuedata.bbox)
##
##    def _valuedatafilter(valuedata, groupfeat):
##        return valuedata.quick_overlap(groupfeat.bbox)
##    
##    def _matchcondition(feat, geom, otherfeat, othergeom):
##        return geom.intersects(othergeom)
##
##    # run
##    summarized = conditional_summary(groupbydata, valuedata,
##                                     matchcondition=_matchcondition,
##                                     groupbyfilter=_groupbyfilter,
##                                     valuedatafilter=_valuedatafilter,
##                                     fieldmapping=fieldmapping,
##                                     prepgeom=True,
##                                     **kwargs)
##
##    return summarized






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
    # See eg http://www.cs.umd.edu/~hjs/pubs/incnear2.pdf

    from . import sql

    out = pg.vector.data.VectorData()

    # insert groupby data fields into fieldmapping
    basefm = [(name,lambda f:f[name],"first") for name in groupbydata.fields]
    fieldmapping = basefm + fieldmapping
    out.fields = [name for name,valfunc,aggfunc in fieldmapping]

    # group by each groupby feature
    iterable = ([(feat,feat.get_shapely()),(otherfeat,otherfeat.get_shapely())]
                for feat in groupbydata for otherfeat in valuedata)
    for group in sql.groupby(iterable, lambda([(f,g),(of,og)]): id(f)):

        # precalc all distances
        group = ([(f,g),(of,og),g.distance(og)] for (f,g),(of,og) in group)

        # sort by nearest dist dirst
        group = sorted(group, key=lambda([(f,g),(of,og),d]): d)

        # filter to only those within radius
        if radius: 
            group = sql.where(group, lambda([(f,g),(of,og),d]): d <= radius)

        # filter ro only n nearest
        if n:
            group = sql.limit(group, n)

        # make iter as usually expected by fieldmapping
        group = ((f,g) for [(f,g),(of,og),d] in group)

        # aggregate and add
        # (not sure if will be correct, in terms of args expected by fieldmapping...?)
        row,geom = sql.aggreg(group, fieldmapping, lambda(itr): next(itr)[1])
        out.add_feature(row, geom)

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












