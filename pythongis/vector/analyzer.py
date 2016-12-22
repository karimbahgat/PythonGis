
import itertools, operator, math
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely






# Overlay Analysis (transfer of values, but no clip)

def overlap_summary(groupbydata, valuedata, fieldmapping=[], keepall=True, valuegroup=None, key=None, **kwargs):
    """
    Summarizes the values of "valuedata" that overlap "groupbydata",
    and adds the summary statistics to the output data.

    "fieldmapping" is a list of ('outfieldname', 'getvaluefunction', 'statistic name or function') tuples that decides which
    variables to summarize and how to do so. Valid statistics are count,
    sum, max, min, and average.

    Key is a function for determining if a pair of features should be processed, taking feat and clipfeat as input args and returning True or False
    """

    from . import sql

    out = VectorData()

    # add fields
    out.fields = list(groupbydata.fields)
    out.fields.extend([name for name,valfunc,aggfunc in fieldmapping])

    # loop
    if not hasattr(groupbydata, "spindex"): groupbydata.create_spatial_index()
    if not hasattr(valuedata, "spindex"): valuedata.create_spatial_index()
    groupfeats = groupbydata if keepall else groupbydata.quick_overlap(valuedata.bbox) # take advantage of spindex if not keeping all
    for groupfeat in groupfeats: 

        # testing
##        if groupfeat["CNTRY_NAME"] not in ("Taiwan",):
##            continue
        
        geom = groupfeat.get_shapely()
        supergeom = supershapely(geom)
        valuefeats = ((valfeat,valfeat.get_shapely()) for valfeat in valuedata.quick_overlap(groupfeat.bbox))

        # aggregate
        if groupbydata.type == valuedata.type == "Polygon":
            # when comparing polys to polys, dont count neighbouring polygons that just touch on the edge
            def overlaps(valgeom):
                if supergeom.intersects(valgeom) and not geom.touches(valgeom):
                    intsec = geom.intersection(valgeom)
                    if not intsec.is_empty and groupbydata.type in intsec.geom_type and intsec.area > 0.00000000001:
                        return True
        else:
            # for lines and points, ok that just touches on the edge
            def overlaps(valgeom):
                return supergeom.intersects(valgeom)
            
        if key:
            matches = (valfeat for valfeat,valgeom in valuefeats
                       if key(groupfeat,valfeat) and overlaps(valgeom))
        else:
            matches = ((valfeat,valgeom) for valfeat,valgeom in valuefeats
                       if overlaps(valgeom))

        # clean potential junk, maybe allow user setting of minimum area (put on hold for now, maybe user should make sure of this in advance?)
        def cleaned():
            for valfeat,valgeom in matches:
##                intsec = geom.intersection(valgeom)
##                if groupbydata.type in intsec.geom_type and intsec.area > 0.00000000001:
##                    yield valfeat
                yield valfeat
        matches = list(cleaned())

        # testing...
##        print "groupfeat",zip(groupbydata.fields,groupfeat.row)
##        groupfeat.view(1000,600,bbox=groupfeat.bbox, fillcolor="red")
##        for vf in matches:
##            print "valfeat",zip(valuedata.fields,vf.row)
##            vf.view(1000,600,bbox=groupfeat.bbox, fillcolor="blue")
##            from .data import Feature
##            intsec = groupfeat.get_shapely().intersection(vf.get_shapely())
##            print intsec.area
##            Feature(groupbydata, [], intsec.__geo_interface__).view(1000,500,bbox=groupfeat.bbox, fillcolor="yellow")

        if valuegroup:
            if matches:
                for group in sql.groupby(matches, valuegroup):
                    aggreg = sql.aggreg(group, fieldmapping)

                    newrow = list(groupfeat.row)
                    newrow.extend( aggreg )
                    out.add_feature(newrow, geom.__geo_interface__)

            elif keepall:
                newrow = list(groupfeat.row)
                newrow.extend( ("" for _ in fieldmapping) )
                out.add_feature(newrow, geom.__geo_interface__)

        else:
            if matches:
                aggreg = sql.aggreg(matches, fieldmapping)

            # add
            if matches:
                newrow = list(groupfeat.row)
                newrow.extend( aggreg )
                out.add_feature(newrow, geom.__geo_interface__)

            elif keepall:
                newrow = list(groupfeat.row)
                newrow.extend( ("" for _ in fieldmapping) )
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












