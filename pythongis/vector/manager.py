
import itertools, operator, math
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely





#############
### IDEA: RESTRUCTURING??
##
### spatial testing (allow shortcut multiple test conditions with multiple datasets as list in the "where" option in select and join methods)
##distance, intersects, within, contains, crosses, touches, equals, disjoint
##
### spatial shapes (allow shortcut multiple shapes specs with multiple datasets as list in the "clip" option in select and join method [eg where=intersects, clip=intersection, or clip=difference or clip=union])
##intersection
##difference
##union (ie collapse)
##
### self: (maybe just via option)
##
### self spatial testing
##
### self spatial shapes
##
################






# Select extract operations

def crop(data, bbox):
    """
    Crops the data by a bounding box.
    Used for quickly focusing data on a subregion.
    """
    
    # create spatial index
    if not hasattr(data, "spindex"): data.create_spatial_index()

    out = VectorData()
    out.fields = list(data.fields)

    bboxgeom = shapely.geometry.box(*bbox)
    iterable = ((feat,feat.get_shapely()) for feat in data.quick_overlap(bbox))
    for feat,geom in iterable:
        intsec = geom.intersection(bboxgeom)
        if not intsec.is_empty:
            out.add_feature(feat.row, intsec.__geo_interface__)

    return out

def where(data, other, condition, **kwargs):
    """
    Locates and returns those features that match some spatial condition
    with another dataset.

    I.e. "spatial select", "select by location". 
    """
    # TODO: Maybe rename "select_where"
    # TODO: Maybe simply add optional "where" option to the basic "select" method,
    # passed as list of data-condition tuples (allowing comparing to multiple layers)
    # The conditions can be defined as separate functions in this module comparing two
    # datas:
    # ie distance, intersects, within, contains, crosses, touches, equals, disjoint. 
    
    # same as select by location
    condition = condition.lower()
    
    # create spatial index
    if not hasattr(data, "spindex"): data.create_spatial_index()
    if not hasattr(other, "spindex"): other.create_spatial_index()

    out = VectorData()
    out.fields = list(data.fields)

    if condition in ("distance",):
        maxdist = kwargs.get("radius")
        if not maxdist:
            raise Exception("The 'distance' select condition requires a 'radius' arg")

        for feat in data:
            geom = feat.get_shapely()
            
            for otherfeat in other:
                othergeom = otherfeat.get_shapely()
                
                if geom.distance(othergeom) <= maxdist:
                    out.add_feature(feat.row, feat.geometry)
                    break  # only one match is needed

        return out

    elif condition in ("intersects", "within", "contains", "crosses", "touches", "equals"):
        for feat in data.quick_overlap(other.bbox):
            geom = feat.get_shapely()
            matchtest = getattr(geom, condition)
            
            for otherfeat in other.quick_overlap(feat.bbox):
                othergeom = otherfeat.get_shapely()
                
                if matchtest(othergeom):
                    out.add_feature(feat.row, feat.geometry)
                    break  # only one match is needed

        return out

    elif condition in ("disjoint",):
        # first add those whose bboxes clearly dont overlap
        for feat in data.quick_disjoint(other.bbox):
            out.add_feature(feat.row, feat.geometry)

        # then check those that might overlap
        for feat in data.quick_overlap(other.bbox):
            geom = feat.get_shapely()

            # has to be disjoint with all those that maybe overlap,
            # ie a feature that intersects at least one feature in the
            # other layer is not disjoint
            disjoint = all((otherfeat.get_shapely().disjoint(geom) for otherfeat in other.quick_overlap(feat.bbox)))

            if disjoint:
                out.add_feature(feat.row, feat.geometry)

        return out
    
    else:
        raise Exception("Unknown select condition")








# File management

def split(data, key, breaks="unique", **kwargs):
    """
    Splits a vector data layer into multiple ones based on a key which can be
    a field name, a list of field names, or a function. The default is to
    create a split for each new unique occurance of the key value, but the
    breaks arg can also be set to the name of other classification algorithms
    or to a list of your own custom break values. The key, breaks, and kwargs
    follow the input and behavior of the Classipy package's split and unique
    functions. 

    Iterates through each new split layer one at a time. 
    """
    
    # TODO: MAYBE SWITCH key TO by
    
    keywrap = key
    if not hasattr(key, "__call__"):
        if isinstance(key,(list,tuple)):
            keywrap = lambda f: tuple((f[k] for k in key))
        else:
            keywrap = lambda f: f[key]

    import classipy as cp
    if breaks == "unique":
        grouped = cp.unique(data, key=keywrap, **kwargs)
    else:
        grouped = cp.split(data, breaks=breaks, key=keywrap, **kwargs)
        
    for splitid,features in grouped:
        outfile = VectorData()
        outfile.fields = list(data.fields)
        for oldfeat in features:
            outfile.add_feature(oldfeat.row, oldfeat.geometry)
        yield splitid,outfile

def merge(*datalist):
    """
    Merges two or more vector data layers, combining all their rows
    and fields into a single table.

    Adds the merged data to the layers list.
    """
    #make empty table
    firstfile = datalist[0]
    outfile = VectorData()
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
            geometry = feature.geometry.copy() if feature.geometry else None
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

def clean(data, tolerance=0, preserve_topology=True):
    """Cleans the vector data of unnecessary clutter such as repeat
    points or closely related points within the distance specified in the
    'tolerance' parameter. Also tries to fix any broken geometries, dropping
    any unfixable ones.

    Adds the resulting cleaned data to the layers list.
    """
    # TODO: MAYBE ADD PRESERVETOPOLOGY OPTION FOR POLYGON TYPE, WHICH CONVERTS TO UNIQUE LINES, THEN CLEANS THE LINES,
    # THEN RECOMBINES BACK TO POLYGONS, THEN REASSIGNS ATTRIBUTES BY JOINING WITH CENTERPOINT OF ORIGINAL SHAPES
    
    # create new file
    outfile = VectorData()
    outfile.fields = list(data.fields)

    # clean
    for feat in data:
        shapelyobj = feat.get_shapely()
        
        # try fixing invalid geoms
        if not shapelyobj.is_valid:
            if "Polygon" in shapelyobj.type:
                # fix bowtie polygons
                shapelyobj = shapelyobj.buffer(0.0)

        # remove repeat points (tolerance=0)
        # (and optionally smooth out complex shapes, tolerance > 0)
        shapelyobj = shapelyobj.simplify(tolerance, preserve_topology=preserve_topology)
            
        # if still invalid, do not add to output
        if not shapelyobj.is_valid:
            continue

        # write to file
        geojson = shapelyobj.__geo_interface__
        outfile.add_feature(feat.row, geojson)

    return outfile

##def selfoverlap(data, primkey):
##    """Clean away any internal overlap of features,
##    using primkey to decide which feature to keep"""
##    # predefined method that performs a common series of operations for
##    # dealing with selfoverlaps, eg get selfintersections then aggregate by duplicates geometries
##    # or get selfintersections then choose one based on priority key
##    # ...
##
##    raise Exception("Not yet implemented")
##
##def snap_to(data, other):
##    """Snaps all vertexes from the features in one layer snap to the vertexes of features in another layer within a certain distance"""
##                           
##    raise Exception("Not yet implemented")

def integrate(data, other):
    """Make features in one layer snap to the edges of features in another layer"""
    # uses key to decide which main features belong to which snapto features
    # remove those main polygon areas that go outside their keyed snapto features
    # for each group of keyed main polygons, make into lines and remove the boundary so only get internal borders
    # then extend dangling lines until reaches the keyed snapto boundaries

    raise Exception("Not yet implemented")






# Create operations

def connect(frompoints, topoints, key=None, greatcircle=True, segments=100):
    """Two point files, and for each frompoint draw line to each topoint
    that matches based on some key value."""

    # get key
    if isinstance(key, (list,tuple)) and len(key) == 2:
        k1,k2 = key
    else:
        k1 = k2 = key # same key for both
    key1 = k1 if hasattr(k1,"__call__") else lambda f:f[k1]
    key2 = k2 if hasattr(k2,"__call__") else lambda f:f[k2]

    from ._helpers import great_circle_path

    # TODO: allow any geometry types via centroids, not just point types
    # ...

    # TODO: optimize with hash lookup table
    # ...
        
    def flatten(data):
        for feat in data:
            if not feat.geometry: continue
            geotype = feat.geometry["type"]
            coords = feat.geometry["coordinates"]
            if "Multi" in geotype:
                for singlepart in coords:
                    geoj = {"type": geotype.replace("Multi", ""),
                            "coordinates": singlepart}
                    yield feat, geoj
            else:
                yield feat, feat.geometry

    # create new file
    outfile = VectorData()
    outfile.fields = list(frompoints.fields)
    outfile.fields.extend(topoints.fields)

    # connect points matching criteria
    for fromfeat,frompoint in flatten(frompoints):
        for tofeat,topoint in flatten(topoints):
            match = key1(fromfeat) == key2(tofeat) if key1 and key2 else True
            if match:
                if greatcircle:
                    linepath = great_circle_path(frompoint["coordinates"], topoint["coordinates"], segments=segments)
                else:
                    linepath = [frompoint["coordinates"], topoint["coordinates"]]
                geoj = {"type": "LineString",
                        "coordinates": linepath}
                row = list(fromfeat.row)
                row.extend(tofeat.row)
                outfile.add_feature(row=row, geometry=geoj)

    return outfile






# Modify operations

def buffer(data, dist, join_style="round", cap_style="round", mitre_limit=1.0, geodetic=False):
    """
    Buffering the data by a positive distance grows the geometry,
    while a negative distance shrinks it. Distance units should be given in
    units of the data's coordinate reference system. 

    Distance is an expression written in Python syntax, where it is possible
    to access the attributes of each feature by writing: feat['fieldname'].
    """
    # get distance func
    if not hasattr(dist, "__call__"):
        distfunc = dist
    else:
        distfunc = lambda f: dist 

    # get buffer func
    if geodetic:
        # geodetic
        if data.type != "Point":
            raise Exception("Geodetic buffer only implemented for points")

        from ._helpers import geodetic_buffer
        def bufferfunc(feat):
            geoj = feat.geometry
            distval = distfunc(feat)
            return geodetic_buffer(geoj, distval, resolution)

    else:
        # geometry
        joincode = {"round":1,
                    "flat":2,
                    "square":3}[join_style]
        capcode = {"round":1,
                    "mitre":2,
                    "bevel":3}[cap_style]
        def bufferfunc(feat):
            geom = feat.get_shapely()
            distval = distfunc(feat)
            buffered = geom.buffer(distval, join_style=joincode, cap_style=capcode, mitre_limit=mitre_limit)
            return buffered.__geo_interface__
        
    # buffer and change each geojson dict in-place
    new = VectorData()
    new.fields = list(data.fields)
    for feat in data:
        buffered = bufferfunc(feat)
        new.add_feature(feat.row, buffered)
        
    # change data type to polygon
    new.type = "Polygon"
    return new


##def collapse(data, by=None, fieldmapping=[], contig=False):
##    """
##    Glue and aggregate features in a single layer with same values.
##    """
##    # aka dissolve
##
##    # for now only designed for polygons
##    # not sure how lines or points will do
##    # ...
##
##    # match requires neighbouring features (intersects/touches) and possibly same key value
##    # also cannot be itself
##
##    # TODO: allow two versions, one where only contiguous areas with same key are considered a stats group
##    # and one considering where all areas with same key regardless of contiguous
##    # ALSO use much faster algorithm if no key, since just need cascaded union on all followed by groupby stats on all
##
##    from . import sql
##
##    if contig: 
##        # contiguous dissolve
##        # requires two combi items in funcs
##        
##        raise Exception("Contiguous dissolve not yet implemented")
##
##        # cheating approach
##        # cascade union on all with same key
##        # then for each single poly in result (ie contiguous),
##        # ...find overlapping orig geoms and aggregate stats
##        # ...and expand single poly by unioning with orig geoms that are multipoly (since those should also be part of the contiguous poly)
##        # just an idea so far
##        # ...
##
##    else:
##        # non-contiguous dissolve
##        # much easier and faster
##        # requires only one combi item in funcs
##
##        # TODO: redo so key and fieldmapping funcs only have to expect the feat obj
##        # maybe by switching away from full sql approach...
##
##        if not by: by = lambda x: True # groups together all items
##
##        def feats():
##            for feat in data:
##                feat._tempgeom = feat.get_shapely() # temporary store it for repeated use
##                yield feat
##
##        def _geomselect(feats):
##            geoms = [feat._tempgeom for feat in feats]
##            
##            union = shapely.ops.cascaded_union(geoms)
##            if not union.is_empty:
##                return union.__geo_interface__
##
##        q = sql.query(_from=[feats()],
##                     _groupby=by,
##                     _select=fieldmapping,
##                     _geomselect=_geomselect,
##                    )
##
##        res = sql.query_to_data(q)
##
##        return res

def cut(data, cutter):
    """
    Cuts apart a layer by the lines of another layer
    """

    # TODO: not sure if correct, quite slow

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
                    holelines = shapely.geometry.MultiLineString([hole.boundary for hole in holes])
                    lines = lines.union(holelines)

            elif "LineString" in cutgeom.type:
                lines = cutgeom
                
            return lines

        cutgeoms = (cutfeat.get_shapely() for cutfeat in cutter.quick_overlap(feat.bbox))
        cutgeoms = (cutgeom for cutgeom in cutgeoms if cutgeom.intersects(geom))
        cutgeoms_lines = [get_as_lines(cutgeom) for cutgeom in cutgeoms]
        cutunion = shapely.ops.cascaded_union(cutgeoms_lines)

        if "Polygon" in geom.type:
            # union main and cutter and make into new polygons
            result = shapely.ops.polygonize(geomlines.union(cutunion))
            polys = list(result)
            if len(polys) == 1:
                newgeom = polys[0]
            else:
                newgeom = shapely.geometry.MultiPolygon(polys)

            # the above only cut from the exterior of the main data,
            # so subtract main data's holes from the results
            if "Multi" in cutgeom.type:
                holes = [hole for multigeom in cutgeom.geoms for hole in multigeom.interiors]
            else:
                holes = cutgeom.interiors
            if holes:
                # subtract from the exterior
                holes = shapely.geometry.MultiPolygon(holes)
                newgeom = newgeom.difference(holes)
                
        elif "LineString" in geom.type:
            raise Exception("Cutting of linestrings not yet implemented")

        # add feature
        outdata.add_feature(feat.row, newgeom.__geo_interface__)
        
    return outdata






# Compare operations

##def intersection(data, clipper, key=None):
##    """
##    Clips the data to the parts that it has in common with the clipper polygon.
##
##    Key is a function for determining if a pair of features should be processed, taking feat and clipfeat as input args and returning True or False
##    """
##
##    # create spatial index
##    if not hasattr(data, "spindex"): data.create_spatial_index()
##    if not hasattr(clipper, "spindex"): clipper.create_spatial_index()
##
##    out = VectorData()
##    out.fields = list(data.fields)
##
##    iterable = ((feat,feat.get_shapely()) for feat in data.quick_overlap(clipper.bbox))
##    for feat,geom in iterable:
##        
##        supergeom = supershapely(geom)
##        iterable2 = ((clipfeat,clipfeat.get_shapely()) for clipfeat in clipper.quick_overlap(feat.bbox))
##
##        for clipfeat,clipgeom in iterable2:
##            if key:
##                if key(feat,clipfeat) and supergeom.intersects(clipgeom) and not geom.touches(clipgeom):
##                    intsec = geom.intersection(clipgeom)
##                    if not intsec.is_empty and data.type in intsec.geom_type and intsec.area > 0.00000000001:                        
##                        out.add_feature(feat.row, intsec.__geo_interface__)
##            else:
##                if supergeom.intersects(clipgeom) and not geom.touches(clipgeom):
##                    intsec = geom.intersection(clipgeom)
##                    if not intsec.is_empty and data.type in intsec.geom_type and intsec.area > 0.00000000001:
##                        out.add_feature(feat.row, intsec.__geo_interface__)
##
##    return out
##
##def difference(data, other):
##    """
##    Finds the parts that are unique to the main data, that it does not
##    have in common with the other data. 
##    """
##    # TODO: Fix ala where("disjoint")
##
##    out = VectorData()
##    out.fields = list(data.fields)
##
##    for feat in data:
##        geom = feat.get_shapely()
##        for otherfeat in other:
##            othergeom = otherfeat.get_shapely()
##            diff = geom.difference(othergeom)
##            if not diff.is_empty:
##                out.add_feature(feat.row, diff.__geo_interface__)
##
##    return out













# FINALLY

# IDEA:
#       data.select
#               .by_attributes()
#               .by_location()
#       data.compare
#               .by_

##def select(data, condition=None):
##    pass

##def modify(data, condition=None, where=None, clip=None):
##    pass

##def link(data, condition=None, where=None, clip=None, linktype="join"):
##    # linktype can also be relate
##    pass




def select(data, condition=None, where=None): # OR attributes=..., location=...
    data.select #...
    data = _where(data, condition=where)
    pass

def clip(data, other, clip_type, condition=None, where=None, by=None):
    """
    Pairwise clip operation between each pair of features. 

    - clip_type: intersection, union, or difference
    """

    # Note: if no by, then pairwise, if by, then accept fieldmapping (and clip_type will be run cumulatively within each group)
    # ie for union/dissolve/collapse, use clip(data, other, "union", by="ID", fieldmapping=...)
    # this way can also specify continguous dissolve, overlapping dissolve, disjoint dissolve, etc via the where param...
    # for isect and diff is different, only geom clip_type will be applied within each group, each row still intact.
    # hmmm...
    
    # create spatial index
    if not hasattr(data, "spindex"): data.create_spatial_index()
    if not hasattr(clipper, "spindex"): clipper.create_spatial_index()

    out = VectorData()
    out.fields = list(data.fields)

    if clip_type == "intersection":
        iterable = ((feat,feat.get_shapely()) for feat in data.quick_overlap(clipper.bbox))
        for feat,geom in iterable:
            
            supergeom = supershapely(geom)
            iterable2 = ((clipfeat,clipfeat.get_shapely()) for clipfeat in clipper.quick_overlap(feat.bbox))

            for clipfeat,clipgeom in iterable2:
                if key:
                    if key(feat,clipfeat) and supergeom.intersects(clipgeom) and not geom.touches(clipgeom):
                        intsec = geom.intersection(clipgeom)
                        if not intsec.is_empty and data.type in intsec.geom_type and intsec.area > 0.00000000001: # replace with optional snapping
                            out.add_feature(feat.row, intsec.__geo_interface__)
                else:
                    if supergeom.intersects(clipgeom) and not geom.touches(clipgeom):
                        intsec = geom.intersection(clipgeom)
                        if not intsec.is_empty and data.type in intsec.geom_type and intsec.area > 0.00000000001: # replace with optional snapping
                            out.add_feature(feat.row, intsec.__geo_interface__)

    elif clip_type == "difference":
        pass

    elif clip_type == "union":
        pass

    return out

def join(data, other, condition=None, where=None, clip=None):
    pass















# Self geometric operations (works on a feature level)...

##def selfintersection(data, primkey):
##    """Clean away any internal overlap of features,
##    using primkey to decide which feature to keep"""
##    # duplicate each feature for each feature it matches with, with a unique geometry for each...
##
##    raise Exception("Not yet implemented")
##
##def selfunion(data, primkey):
##    """Clean away any internal overlap of features,
##    using primkey to decide which feature to keep"""
##    # duplicate each feature for each feature it matches with, with a unique geometry for each...
##
##    raise Exception("Not yet implemented")
##
##def selfdifference(data, primkey):
##    """Clean away any internal overlap of features,
##    using primkey to decide which feature to keep"""
##    # duplicate each feature for each feature it matches with, with a unique geometry for each...
##
##    raise Exception("Not yet implemented")















########## UNSURE ... 

##def cumulative_selfintersections(self):
##    # cuts every feature by the intersections with all other features
##    if not hasattr(self, "spindex"):
##        self.create_spatial_index()
##    
##    out = VectorData()
##    out.type = self.type
##    out.fields = list(self.fields)
##    geoms = dict(((f.id,f.get_shapely()) for f in self))
##
##
##    def getisecs(g, geoms):
##        isecs = []
##        for og in geoms:
##            #if og.area < 0.001: continue # this somehow makes it work....????
##            if id(og) != id(g):
##                #print "testing", id(g), id(og)
##                isec_bool = og.equals(g) or (og.intersects(g) and not og.touches(g)) #og.crosses(g) or og.contains(g) or og.within(g) # not those that touch or equals
##                if isec_bool:
##                    isec = g.intersection(og)
##
##                    # sifting through dongles etc approach
####                        incl = []
####                        if isec.geom_type == "GeometryCollection":
####                            # only get same types, ie ignore dongles etc
####                            incl.extend([sub for sub in isec.geoms if out.type in sub.geom_type])
####                        elif out.type in isec.geom_type:
####                            # only if same type
####                            incl.append(isec)
####                        #viewisecs(g, [og], "pair isec = %s, include = %s" % (isec_bool,bool(incl)) )
####                        for sub in incl:
####                            #REMEMBER: this is only the immediate pairwise isecs, and might be further subdivided
####                            #viewisecs(g, [og], "pair isec = %s" % isec_bool)
####                            print repr(sub)
####                            isecs.append( sub )
##
##                    # only pure approach
##                    #print repr(isec)
##                    if out.type in isec.geom_type:
##                        #print "included for next step"
##                        isecs.append(isec)
##                        
####                        else:
####                            ###isecs.append(og)
####                            if hasattr(isec, "geoms"):
####                                for i in isec.geoms:
####                                    if out.type in i.geom_type and i.area >= 0.0001:
####                                        print str(i)[:200]
####                                        viewisecs(i, [], str(i.area) + " inside geomcollection, valid = %s" % i.is_valid)
####                                #viewisecs(og, [i for i in isec.geoms if out.type in i.geom_type], "wrong type")
##
##                else:
##                    pass #viewisecs(g, [og], "isec_bool False")
##                        
##        return isecs
##
##    DEBUG = False
##
##    def viewisecs(g=None, isecs=None, title="[Title]"):
##        if DEBUG: 
##            from ..renderer import Map, Color
##            mapp = Map(width=1000, height=1000, title=title)
##
##            if isecs:
##                d = VectorData()
##                d.fields = ["dum"]
##                for i in isecs:
##                    d.add_feature([1], i.__geo_interface__)
##                mapp.add_layer(d, fillcolor="blue")
##
##            if g:
##                gd = VectorData()
##                gd.fields = ["dum"]
##                gd.add_feature([1], g.__geo_interface__)
##                mapp.add_layer(gd, fillcolor=Color("red",opacity=155))
##
##            mapp.zoom_auto()
##            mapp.view()
##
####        finals = []
####        compare = [f.get_shapely() for f in self]
####        for feat in self:
####            print feat
####            geom = geoms[feat.id]
####            compare = getisecs(geom, compare)
####            for sub in compare:
####                finals.append((feat,sub))
####        for feat,geom in finals:
####            out.add_feature(feat.row, geom.__geo_interface__)
##
##    def process(isecs):
##        parts = []
##        for g in isecs:
##            subisecs = getisecs(g, isecs)
##            viewisecs(g, [], "getting subisecs of g")
##            viewisecs(None, isecs, "compared to ...")
##            if not subisecs:
##                viewisecs(g, [], "node (g) reached, adding" )
##                parts += [g]
##            elif len(subisecs) == 1:
##                viewisecs(subisecs[0], [], "node (subisec) reached, adding" )
##                parts += [subisecs[0]]
##            else:
##                viewisecs(None, subisecs, "going deeper, len = %s" % len(subisecs) )
##                parts += process(subisecs)
##                #viewisecs(g, subisecs, str(len(subisecs)) + " were returned as len = %s" % len(parts) )
##        return parts
##
##    for i,feat in enumerate(self):
##        #if feat["CNTRY_NAME"] != "Russia": continue
##        #if i >= 10:
##        #    return out
##        print feat
##        geom = geoms[feat.id]
##        top_isecs = [geoms[otherfeat.id] for otherfeat in self.quick_overlap(feat.bbox)]
##        
##        #print self.select(lambda f:f["CNTRY_NAME"]=="USSR")
##        #top_isecs = [next((f.get_shapely() for f in self.select(lambda f:f["CNTRY_NAME"]=="USSR")))]
##        #print "spindex",top_isecs
##        #from ..renderer import Color
##        #self.select(lambda f:f["CNTRY_NAME"]=="USSR").view(1000,1000,flipy=1,fillcolor=Color("red",opacity=155))
##        #viewisecs(geom, top_isecs, "spindex to be tested for isecs")
##        
##        top_isecs = getisecs(geom, top_isecs)
##        print "top_isecs",top_isecs
##        viewisecs(geom, top_isecs, "spindex verified, len = %s" % len(top_isecs) )
##        parts = process(top_isecs)
##        for g in parts:
##            print "adding", id(g)
##            #viewisecs(g, [], "final isec")
##            out.add_feature(feat.row, g.__geo_interface__)
##    
##
####        for feat in self:
####            print feat
####            geom = geoms[feat.id]
####            # find all othergeoms that 
####            othergeoms = (geoms[f.id] for f in self.quick_overlap(feat.bbox))
####            othergeoms = [og for og in othergeoms if og.intersects(geom)]
####            for othergeom in othergeoms:
####                intsec = geom.intersection(othergeom)
####                if not intsec.is_empty and self.type in intsec.geom_type:
####                    print intsec.geom_type
####                    out.add_feature(feat.row, intsec.__geo_interface__)
####                    out.view(1000, 1000, flipy=1)
##
##
####        def cutup(geom, othergeoms):
####            parts = []
####            for othergeom in othergeoms:
####                # add intsecs
####                if geom != othergeom and geom.intersects(othergeom):
####                    intsec = geom.intersection(othergeom)
####                    if not intsec.is_empty:
####                        parts.append(intsec)
####            # add diff
####            diff = geom.difference(shapely.ops.cascaded_union(parts))
####            if not diff.is_empty:
####                parts.append(diff)
####            return parts
####
####        def subparts(geoms):
####            subs = []
####            for geom in geoms:
####                subs += cutup(geom, geoms)
####            return subs
####
####        def recur(geoms):
####            prevparts = []
####            parts = subparts(geoms)
####            while len(parts) != len(prevparts):
####                print len(parts)
####                prevparts = list(parts)
####                parts = subparts(parts)
####                break
####            return parts
####                
####        for feat in self:
####            geom = geoms[feat.id]
####            # find all othergeoms that 
####            othergeoms = (geoms[f.id] for f in self.quick_overlap(feat.bbox))
####            othergeoms = [og for og in othergeoms if og.intersects(geom)]
####            print feat
####            parts = recur([geom]+othergeoms)
####            print len(parts)
##
##
####        def flatten(geom):
####            if "Multi" in geom.geom_type:
####                for g in geom.geoms:
####                    yield g
####            else:
####                yield geom
####        for feat in self:
####            geom = geoms[feat.id]
####            # find all othergeoms that 
####            othergeoms = []
####            for otherfeat in self.quick_overlap(feat.bbox):
####                if otherfeat == feat: continue
####                if not geoms[otherfeat.id].intersects(geom): continue
####                othergeoms += list(flatten(geoms[otherfeat.id]))
####            # combine into one so only have to make one spatial test
####            if "Polygon" in self.type:
####                othergeom = shapely.geometry.MultiPolygon(othergeoms)
####            elif "LineString" in self.type:
####                othergeom = shapely.geometry.MultiLineString(othergeoms)
####            elif "Point" in self.type:
####                othergeom = shapely.geometry.MultiPoint(othergeoms)
####            else:
####                raise Exception()
####            print all((g.is_valid for g in othergeoms))
####            print othergeom.is_valid
####            # add intsecs
####            intsec = geom.intersection(othergeom)
####            if not intsec.is_empty:
####                for g in flatten(intsec):
####                    out.add_feature(feat.row, g)
####            # add diffs
####            diff = geom.difference(othergeom)
####            if not diff.is_empty:
####                for g in flatten(diff):
####                    out.add_feature(feat.row, g)
##
##    return out



