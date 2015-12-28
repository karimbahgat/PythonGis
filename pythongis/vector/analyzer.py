
import itertools, operator
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely



# TODO: REDO OVERLAP AND NEAREST SUMMARY USING SQL FUNCS
        
# Spatial relations summary
# (somewhat lowlevel but provided for advanced and flexible use-cases)

def conditional_summary(groupbydata, valuedata, matchcondition,
                        groupbyfilter=None, valuedatafilter=None,
                        fieldmapping=[], keepall=True, 
                        max_n=None, prepgeom=False):
    
    data1,data2 = groupbydata,valuedata

    # if no filter, main data is always first arg so return first item unfiltered
    if not groupbyfilter: groupbyfilter = lambda gd,vd: gd
    if not valuedatafilter: valuedatafilter = lambda vd,gf: vd

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

        # get all value features that match a condition
        n = 0
        for otherfeat in valuedatafilter(data2, feat): 
            othergeom = otherfeat.get_shapely()
            if matchcondition(feat, geom, otherfeat, othergeom):
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
    
    def _matchcondition(feat, geom, otherfeat, othergeom):
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
    
    def _matchcondition(feat, geom, otherfeat, othergeom):
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

def glue(data, key=None, fieldmapping=[], contig=False):   
    # aka dissolve
    # aggregate/glue together features in a single layer with same values

    # for now only designed for polygons
    # not sure how lines or points will do
    # ...

    # match requires neighbouring features (intersects/touches) and possibly same key value
    # also cannot be itself

    # TODO: allow two versions, one where only contiguous areas with same key are considered a stats group
    # and one considering where all areas with same key regardless of contiguous
    # ALSO use much faster algorithm if no key, since just need cascaded union on all followed by groupby stats on all

    from . import sql
    iterable = ((feat,feat.get_shapely()) for feat in data)

    if contig: 
        # contiguous dissolve
        # requires two combi items in funcs
        iterable2 = ((feat,feat.get_shapely()) for feat in data)

        raise Exception("Contiguous dissolve not yet implemented")

        # old version
        # not yet correct, includes all pairs that are contiguous but not guaranteed within same group
        # ...
        
##        if not key: key = lambda x: True # groups together all items
##
##        def _where(itemcombi):
##            (feat,geom),(feat2,geom2) = itemcombi
##            
##            _notsame = feat != feat2
##            if not _notsame: return False
##
##            _bothkey = key([(feat,geom),(feat2,geom2)]) == key([(feat2,geom2),(feat,geom)])
##            if not _bothkey: return False
##
##            _intsec = geom.intersects(geom2)
##            if not _intsec: return False
##            
##            return True
##
##        def _geomselect(itemcombis):
##            geoms = []
##
##            # part of contiguous if intersects any previous pairs
##            for (f11,g11),(f12,g12) in itemcombis:
##                for (f21,g21),(f22,g22) in itemcombis:
##                    _leftleft = g11 != g21 and g11.intersects(g21)
##                    if _leftleft:
##                        geoms.append(g11)
##                        print f11["CNTRY_NAME"]
##                        break
##
##                    _leftright = g11 != g22 and g11.intersects(g22)
##                    if _leftright:
##                        geoms.append(g11)
##                        print f11["CNTRY_NAME"]
##                        break
##
##                    _rightleft = g12 != g21 and g12.intersects(g21)
##                    if _rightleft:
##                        geoms.append(g12)
##                        print f12["CNTRY_NAME"]
##                        break
##
##                    _rightright = g12 != g22 and g12.intersects(g22)
##                    if _rightright:
##                        geoms.append(g12)
##                        print f12["CNTRY_NAME"]
##                        break
##            
##            union = shapely.ops.cascaded_union(geoms)
##            if not union.is_empty:
##                return union.__geo_interface__
##        
##        q = sql.query(_from=[iterable,iterable2],
##                     _groupby=key,
##                     _where=_where,
##                     _select=fieldmapping,
##                     _geomselect=_geomselect,
##                    )
##
##        res = sql.query_to_data(q)
##
##        return res



        # try manual sql component approach
        # not yet done
        # ...
        
##        if not key: key = lambda x: True # groups together all items
##
##        # rename args
##        iterables = [iterable1,iterable2]
##        columnfuncs = _fieldmapping
##        condition = _where
##        geomfunc = _geomselect
##        condition = _where
##        key = key
##
##        # make an iterable that yields every combinaion of all input iterables' items
##        iterable = itertools.product(*iterables)
##
##        # iterate and add
##        groups = groupby(iterable, key)
##        
##        for items in groups:
##            # filter
##            items = where(items, condition)
##                
##            # aggregate
##            # NOTE: columnfuncs and geomfunc must expect an iterable as input and return a single row,geom pair
##            row,geom = aggreg(items, columnfuncs, geomfunc)
##
##            # add feat
##            # ...


        # cheating approach
        # cascade union on all with same key
        # then for each single poly in result (ie contiguous),
        # ...find overlapping orig geoms and aggregate stats
        # ...and expand single poly by unioning with orig geoms that are multipoly (since those should also be part of the contiguous poly)
        # just an idea so far
        # ...



    else:
        # noncontiguous dissolve
        # much easier and faster
        # requires only one combi item in funcs

        if not key: key = lambda x: True # groups together all items

        def _geomselect(itemcombis):
            geoms = []
            for combi in itemcombis:
                f,g = combi[0]
                ###print f["CNTRY_NAME"]
                geoms.append(g)
            
            union = shapely.ops.cascaded_union(geoms)
            if not union.is_empty:
                return union.__geo_interface__

        q = sql.query(_from=[iterable],
                     _groupby=key,
                     _select=fieldmapping,
                     _geomselect=_geomselect,
                    )

        res = sql.query_to_data(q)

        return res


def cut(data, cutter):
    """cut apart a layer by the lines of another layer"""

    # FOR NOW, only cuts poly by poly or poly by line
    # not yet handling line by line, how to do that...?
    # ...

    outdata = VectorData()
    outdata.fields = list(data.fields)

    # point data cannot be cut or used for cutting
    if "Point" in data.type or "Point" in cutter.type:
        raise Exception("Point data cannot be cut or used for cutting, only polygons or lines")

    # create spatial index
    if not hasattr(data, "spindex"): data.create_spatial_index()
    if not hasattr(cutter, "spindex"): cutter.create_spatial_index()

    # cut
    for feat in data.quick_overlap(cutter.bbox):
        geom = feat.get_shapely()

        # if polygon, main geom should be just the exterior without holes
        if "Polygon" in geom.type:
            geomlines = geom.boundary
        elif "LineString" in geom.type:
            geomlines = geom

        # get and prep relevant cut lines
        def get_as_lines(cutgeom):
            if "Polygon" in cutgeom.type:
                # exterior boundary
                lines = cutgeom.boundary
                
                # holes should also be used for cutting
                if "Multi" in cutgeom.type:
                    holes = [hole for multigeom in cutgeom.geoms for hole in multigeom.interiors]
                else:
                    holes = cutgeom.interiors
                if holes:
                    # combine with exterior
                    holelines = MultiLineString([hole.boundary for hole in holes])
                    lines = lines.union(holelines)

            elif "LineString" in cutgeom.type:
                lines = cutgeom
                
            return lines

        cutgeoms = (cutfeat.get_shapely() for cutfeat in cutter.quick_overlap(feat.bbox))
        cutgeoms = (cutgeom for cutgeom in cutgeoms if cutgeom.intersects(geom))
        cutgeoms_lines = [get_as_lines(cutgeom) for cutgeom in cutgeoms]
        cutunion = shapely.ops.cascaded_union(cutgeoms_lines)

        # union main and cutter and make into new polygons
        result = shapely.ops.polygonize(geomlines.union(cutunion))
        polys = list(result)
        if len(polys) == 1:
            newgeom = polys[0]
        else:
            newgeom = shapely.geometry.MultiPolygon(polys)

        # the above only cut from the exterior of the main data,
        # so subtract main data's holes from the results
        if "Polygon" in geom.type:
            if "Multi" in cutgeom.type:
                holes = [hole for multigeom in cutgeom.geoms for hole in multigeom.interiors]
            else:
                holes = cutgeom.interiors
            if holes:
                # subtract from the exterior
                holes = MultiPolygon(holes)
                newgeom = newgeom.difference(holes)

        # add feature
        outdata.add_feature(feat.row, newgeom.__geo_interface__)
        
    return outdata






# Select extract operations

##def crop():
##    # aka intersects(), aka select()
##    # keeps only those that intersect with other layer
##    # similar to intersection() except doesnt alter any geometries
##    pass

def clip(data, clipper):
    # aka intersection without attribute joining
    # how to behave if data is polygon and clipper is linestring
    # perhaps use the cut algorithm, ie merge the two
    # ...


    # create spatial index
    if not hasattr(data, "spindex"): data.create_spatial_index()
    if not hasattr(clipper, "spindex"): clipper.create_spatial_index()

    out = VectorData()
    out.fields = list(data.fields)

    iterable = ((feat,feat.get_shapely()) for feat in data.quick_overlap(clipper.bbox))
    for feat,geom in iterable:
        iterable2 = ((clipfeat,clipfeat.get_shapely()) for clipfeat in clipper.quick_overlap(feat.bbox))
        for clipfeat,clipgeom in iterable2:
            if geom.intersects(clipgeom):
                intsec = geom.intersection(clipgeom)
                out.add_feature(feat.row, intsec.__geo_interface__)

    return out




# Geometrics
# but if handling multiple datas, not sure which attr to keep and when.
# ...

##def intersection(*datas):
##    # aka raster clip
##    pass
##
##    ##    import itertools
##    ##    zip = itertools.izip
##    ##    
##    ##    new = VectorData()
##    ##    new.fields = list((d.fields for d in datas))
##    ##
##    ##    for feat in datas[0]:
##    ##        # get the cumulative intersection of all feats
##    ##        geom = feats[0].get_shapely()
##    ##        for feat in feats[1:]:
##    ##            geom = geom.intersection(feat.get_shapely())
##    ##
##    ##        # collect the rows too maybe?
##    ##        # ...
##    ##        
##    ##        if not geom.is_empty:
##    ##            geojson = geom.__geo_interface__
##    ##            geojson["type"] = geom.type
##    ##            new.add_feature([], geojson)
##    ##
##    ##    # change data type to minimum dimension
##    ##    new.type = "Polygon" 
##    ##    return new
##
##def union(*datas):
##    pass
##
##def unique(*datas):
##    """Those parts of the geometries that are unique(nonintersecting) for each layer.
##    Aka symmetrical difference.
##    """
##    pass

def buffer(data, dist_expression, join_style="round", cap_style="round", mitre_limit=1.0):
    """
    Buffering the data by a positive distance grows the geometry,
    while a negative distance shrinks it. Distance units should be given in
    units of the data's coordinate reference system. 

    Distance is an expression written in Python syntax, where it is possible
    to access the attributes of each feature by writing: feat['fieldname'].
    """
    joincode = {"round":1,
                "flat":2,
                "square":3}[join_style]
    capcode = {"round":1,
                "mitre":2,
                "bevel":3}[cap_style]
    # buffer and change each geojson dict in-place
    new = VectorData()
    new.fields = list(data.fields)
    for feat in data:
        geom = feat.get_shapely()
        dist = eval(dist_expression)
        buffered = geom.buffer(dist, join_style=joincode, cap_style=capcode, mitre_limit=mitre_limit)
        if not buffered.is_empty:
            geojson = buffered.__geo_interface__
            geojson["type"] = buffered.type
            new.add_feature(feat.row, geojson)
    # change data type to polygon
    new.type = "Polygon"
    return new


