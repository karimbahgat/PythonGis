
import itertools, operator
from .data import *

import shapely
from shapely.prepared import prep as supershapely




# Overlay Analysis (transfer of values, but no clip)

def overlap_summary(groupbydata, valuedata, fieldmapping=[]):
    """
    Summarizes the values of "valuedata" that overlap "groupbydata",
    and adds the summary statistics to the output data.

    "fieldmapping" is a list of ('fieldname', 'statistic') tuples that decides which
    variables to summarize and how to do so. Valid statistics are count,
    sum, max, min, and average. 
    """
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
    new = VectorData()
    new.fields = list(data1.fields)
    if fieldmapping: 
        for aggfield,aggtype in fieldmapping:
            new.fields.append(aggfield)

    # for each groupby feature
    for i,feat in enumerate(data1.quick_overlap(data2.bbox)):
        geom = feat.get_shapely()
        geom = supershapely(geom)
        matches = []

        # get all value features that intersect
        for otherfeat in data2.quick_overlap(feat.bbox):        
            othergeom = otherfeat.get_shapely()
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





