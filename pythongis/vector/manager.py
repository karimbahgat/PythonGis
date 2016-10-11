
import itertools, operator, math
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely





# Manager

class _Manager(object):
    "Helps the data instances access this module's functions without having to use self as an arg"
    # TODO: Doesnt really work yet...
    def __init__(self, data):
        self.data = data

        for k,v in globals().items():
            if hasattr(v, "__call__"):
                func = v
                def wrapfunc(*args, **kwargs):
                    # wrap method to insert self data as the first arg
                    args = [self.data] + list(args)
                    return func(*args, **kwargs)
                wrapfunc.__name__ = func.__name__
                wrapfunc.__doc__ = func.__doc__
                
                self.__dict__[k] = wrapfunc

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
    """
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
        for feat in data:
            geom = feat.get_shapely()
            
            for otherfeat in other:
                othergeom = otherfeat.get_shapely()
                
                if geom.disjoint(othergeom):
                    out.add_feature(feat.row, feat.geometry)
                    break  # only one match is needed

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

def clean(data, tolerance=0):
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
        shapelyobj = shapelyobj.simplify(tolerance)
            
        # if still invalid, do not add to output
        if not shapelyobj.is_valid:
            continue

        # write to file
        geojson = shapelyobj.__geo_interface__
        outfile.add_feature(feat.row, geojson)

    return outfile

def selfoverlap(data, primkey):
    """Clean away any internal overlap of features,
    using primkey to decide which feature to keep"""

    raise Exception("Not yet implemented")

def integrate(data, snapto):
    """Make features in one layer snap to the edges of features in another layer"""
    # uses key to decide which main features belong to which snapto features
    # remove those main polygon areas that go outside their keyed snapto features
    # for each group of keyed main polygons, make into lines and remove the boundary so only get internal borders
    # then extend dangling lines until reaches the keyed snapto boundaries

    raise Exception("Not yet implemented")






# Create operations

def connect(frompoints, topoints, k1=None, k2=None, greatcircle=True, segments=100):
    """Two point files, and for each frompoint draw line to each topoint
    that matches based on some key value."""

    from ._helpers import great_circle_path

    # TODO: swithc k1,k2 to a single key function

    # TODO: allow any geometry types via centroids, not just point types
    # ...
    
    key1,key2 = k1,k2
    if key1 and not hasattr(key1, "__call__"):
        key1 = lambda f: f[k1]
    if key2 and not hasattr(key2, "__call__"):
        key2 = lambda f: f[k2]

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

def buffer_geodetic(data, dist_expression, resolution=100):
    """Only for points for now"""
    from ._helpers import geodetic_buffer
    
    if "Point" in data.type:
        new = VectorData()
        new.fields = list(data.fields)
        for feat in data:
            geoj = feat.geometry
            dist = eval(dist_expression)
            assert dist > 0
            buffered = geodetic_buffer(geoj, dist, resolution)
            new.add_feature(feat.row, buffered)
        # change data type to polygon
        new.type = "Polygon"
        return new

    else:
        raise Exception("Geodetic buffer only implemented for points")

def collapse(data, by=None, fieldmapping=[], contig=False):
    """
    Glue and aggregate features in a single layer with same values.
    """
    # aka dissolve

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
        
        raise Exception("Contiguous dissolve not yet implemented")

        # cheating approach
        # cascade union on all with same key
        # then for each single poly in result (ie contiguous),
        # ...find overlapping orig geoms and aggregate stats
        # ...and expand single poly by unioning with orig geoms that are multipoly (since those should also be part of the contiguous poly)
        # just an idea so far
        # ...

    else:
        # non-contiguous dissolve
        # much easier and faster
        # requires only one combi item in funcs

        # TODO: redo so key and fieldmapping funcs only have to expect the feat obj
        # maybe by switching away from full sql approach...

        if not by: by = lambda x: True # groups together all items

        def _geomselect(itemcombis):
            geoms = []
            for combi in itemcombis:
                f,g = combi[0]
                geoms.append(g)
            
            union = shapely.ops.cascaded_union(geoms)
            if not union.is_empty:
                return union.__geo_interface__

        q = sql.query(_from=[iterable],
                     _groupby=by,
                     _select=fieldmapping,
                     _geomselect=_geomselect,
                    )

        res = sql.query_to_data(q)

        return res

def cut(data, cutter):
    """
    Cuts apart a layer by the lines of another layer
    """

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
                holes = MultiPolygon(holes)
                newgeom = newgeom.difference(holes)
                
        elif "LineString" in geom.type:
            raise Exception("Cutting of linestrings not yet implemented")

        # add feature
        outdata.add_feature(feat.row, newgeom.__geo_interface__)
        
    return outdata






# Compare operations

def intersection(data, clipper, key=None):
    """
    Clips the data to the parts that it has in common with the clipper polygon.

    Key is a function for determining if a pair of features should be processed, taking feat and clipfeat as input args and returning True or False
    """

    # create spatial index
    if not hasattr(data, "spindex"): data.create_spatial_index()
    if not hasattr(clipper, "spindex"): clipper.create_spatial_index()

    out = VectorData()
    out.fields = list(data.fields)

    iterable = ((feat,feat.get_shapely()) for feat in data.quick_overlap(clipper.bbox))
    for feat,geom in iterable:
        supergeom = supershapely(geom)
        iterable2 = ((clipfeat,clipfeat.get_shapely()) for clipfeat in clipper.quick_overlap(feat.bbox))
        for clipfeat,clipgeom in iterable2:
            if key and key(feat,clipfeat):
                if supergeom.intersects(clipgeom):
                    intsec = geom.intersection(clipgeom)
                    if not intsec.is_empty:
                        out.add_feature(feat.row, intsec.__geo_interface__)

    return out

def difference(data, other):
    """
    Finds the parts that are unique to the main data, that it does not
    have in common with the other data. 
    """

    out = VectorData()
    out.fields = list(data.fields)

    for feat in data:
        geom = feat.get_shapely()
        for otherfeat in other:
            othergeom = otherfeat.get_shapely()
            diff = geom.difference(othergeom)
            if not diff.is_empty:
                out.add_feature(feat.row, diff.__geo_interface__)

    return out









