
import itertools, operator, math
import warnings
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.geometry import asShape as geojson2shapely
from shapely.prepared import prep as supershapely

import pycrs

from ._helpers import geodetic_buffer






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

def tiled(data, tilesize=None, tiles=(5,5)):
    width = abs(data.bbox[2] - data.bbox[0])
    height = abs(data.bbox[3] - data.bbox[1])
    
    if tilesize:
        tw,th = tilesize

    elif tiles:
        tw,th = width / float(tiles[0]), height / float(tiles[1])

    startx,starty,stopx,stopy = data.bbox

    def _floatrange(fromval,toval,step):
        "handles both ints and flots"
        # NOTE: maybe not necessary to test low-high/high-low
        # since vector bbox is always min-max
        val = fromval
        if fromval < toval:
            while val <= toval:
                yield val, val+step
                val += step
        else:
            while val >= toval:
                yield val, val-step
                val -= step
    
    for y1,y2 in _floatrange(starty, stopy, th):
        y2 = y2 if y2 <= stopy else stopy # cap
        for x1,x2 in _floatrange(startx, stopx, tw):
            x2 = x2 if x2 <= stopx else stopx # cap
            tile = crop(data, [x1,y1,x2,y2])
            if len(tile) > 0:
                yield tile

def where(data, other, condition, **kwargs):
    """
    Locates and returns those features that match some spatial condition
    with another dataset.

    I.e. "spatial select", "select by location". 
    """
    # TODO: Maybe should only be "join" and "where"...
    
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

def spatial_join(data, other, condition, subkey=None, keepall=False, clip=False, **kwargs):
    """
    Pairwise joining with all unique pairs that match the spatial "condition" and the optional "subkey" function.
    Returns a new spatially joined dataset.

    Note: if the other dataset has fields with the same name as the main dataset, those will not be joined, keeping
        only the ones in the main dataset. 

    Arguments:
        data: The main VectorData dataset to be joined to.
        other: The other VectorData dataset to join to the main one.
        condition: The spatial condition required for joining a pair of features.
            Valid options include:
                - "distance" (along with "radius" and/or "n" args)
                - "intersects", "within", "contains", "crosses", "touches", "equals", "covers"
                - "disjoint"
        subkey (optional): If set, acts as an additional non-spatial condition. Only the pairs that pass this condition
            will be tested for the spatial condition. Specified as a function that takes a pair of features as its argument,
            and returns True if they should be joined.
        keepall (optional): If True, keeps all features in the main dataset regardless (default), otherwise only keeps the 
            ones that match.
        clip (optional): If the user is interested in the unique spatial relationship of each feature, the clip argument can
            be used to clip or alter the geometry of each joined pair. The default behavior is for each joined pair to get the
            geometry of the original left feature. 

            Valid values include "intersection", "difference", "union", or a function
            expecting two features and returning a GeoJSON dict or None, which will be performed on the joined geometries.

            The clip argument can also be used to ignore geometries alltogether, especially since joins
            with many matching pairs and duplicate geometries may lead to a large memory footprint. To reduce the memory footprint,
            the clip argument can be set to a function that returns None, returning a non-spatial table without geometries. 
    """

    # TODO: switch if point is other

    # NEW
    condition = condition.lower()
    
    # create spatial index
    if not hasattr(data, "spindex"): data.create_spatial_index()
    if not hasattr(other, "spindex"): other.create_spatial_index()

    out = VectorData()
    out.fields = list(data.fields)
    out.fields += (field for field in other.fields if field not in data.fields)
    
    otheridx = [i for i,field in enumerate(other.fields) if field not in data.fields]

    if isinstance(clip, basestring):
        clipname = clip
        
        # determine correct output type for each operation
        if clipname == 'intersection':
            # lowest dimension
            if 'Point' in (data.type,other.type):
                newtyp = 'Point'
                newmultiobj = shapely.geometry.MultiPoint
            elif 'LineString' in (data.type,other.type):
                newtyp = 'LineString'
                newmultiobj = shapely.geometry.MultiLineString
            elif 'Polygon' in (data.type,other.type):
                newtyp = 'Polygon'
                newmultiobj = shapely.geometry.MultiPolygon
        elif clipname == 'union':
            # highest dimension
            if 'Polygon' in (data.type,other.type):
                newtyp = 'Polygon'
                newmultiobj = shapely.geometry.MultiPolygon
            elif 'LineString' in (data.type,other.type):
                newtyp = 'LineString'
                newmultiobj = shapely.geometry.MultiLineString
            elif 'Point' in (data.type,other.type):
                newtyp = 'Point'
                newmultiobj = shapely.geometry.MultiPoint
        elif clipname == 'difference':
            # same as main
            newtyp = data.type
            if 'Point' in newtyp: newmultiobj = shapely.geometry.MultiPoint
            elif 'LineString' in newtyp: newmultiobj = shapely.geometry.MultiLineString
            elif 'Polygon' in newtyp: newmultiobj = shapely.geometry.MultiPolygon

        print newtyp,newmultiobj
            
        def clip(f1,f2):
            clipfunc = getattr(f1.get_shapely(), clipname)
            #print 'clipping feat'
            try:
                geom = clipfunc(f2._shapely)
            except shapely.errors.TopologicalError:
                warnings.warn('A clip operation failed due to invalid geometries, replacing with null-geometry')
                return None
                
            if geom:
                #print geom.geom_type
                if geom.geom_type == 'GeometryCollection':
                    # only get the subgeoms corresponding to the right type
                    sgeoms = [g for g in geom.geoms if g.geom_type == newtyp] # single geoms
                    mgeoms = [g for g in geom.geoms if g.geom_type == 'Multi'+newtyp] # multi geoms
                    flatmgeoms = [g for mg in mgeoms for g in mg.geoms] # flatten multigeoms
                    geom = newmultiobj(sgeoms + flatmgeoms)
                    return geom.__geo_interface__
                elif newtyp in geom.geom_type:
                    # normal
                    return geom.__geo_interface__
                else:
                    # ignore wrong types
                    return None            

    if condition in ("distance",):
        radius = kwargs.get("radius")
        n = kwargs.get("n")
        geodetic = kwargs.get("geodetic", True)
        if not (radius or n):
            raise Exception("The 'distance' join condition requires a 'radius' or 'n' arg")

        # prep geoms in other
        for otherfeat in other:
            if not otherfeat.geometry:
                continue
            otherfeat._shapely = otherfeat.get_shapely()

        # match funcs
        def within(feat, other):
            if geodetic:
                buff = geojson2shapely(geodetic_buffer(feat.geometry, radius))
            else:
                buff = geom.buffer(radius)
            superbuff = supershapely(buff)
            otherfeats = other.quick_overlap(buff.bounds) if hasattr(other, "spindex") else other
            for otherfeat in otherfeats:
                if superbuff.intersects(otherfeat._shapely):
                    yield otherfeat

        def nearest(feat, otherfeats):
            # TODO: implement optional geodetic distance
            for otherfeat in sorted(otherfeats, key=lambda otherfeat: geom.distance(otherfeat._shapely)):
                yield otherfeat

        # begin
        for feat in data:

            #print feat
            
            if not feat.geometry:
                if keepall:
                    newrow = list(feat.row)
                    newrow += (None for i in otheridx)
                    out.add_feature(newrow, None)
                continue

            geom = feat.get_shapely()
            supergeom = supershapely(geom)

            # test conditions
            # first find overlaps
            overlaps = []
            nonoverlaps = []
            for otherfeat in other.quick_overlap(feat.bbox):
                if subkey and not subkey(feat,otherfeat):
                    continue
                if supergeom.intersects(otherfeat._shapely):
                    overlaps.append(otherfeat)
                else:
                    nonoverlaps.append(otherfeat)
                if n and len(overlaps) >= n:
                    # check if sufficient
                    break
            
            # otherwise proceed to nonoverlaps
            matches = overlaps
            proceed = len(matches) < n if n else True
            if proceed:
                # limit to those within radius
                if radius:
                    # test within
                    # NOTE: seems faster to just use existing spindex and exclude those already added
                    nonoverlaps = (otherfeat for otherfeat in within(feat, other)
                                   if otherfeat not in matches)
                # add remainder of nonoverlaps
                else:
                    for otherfeat in other.quick_disjoint(feat.bbox):
                        nonoverlaps.append(otherfeat)
                # filter by key
                if subkey:
                    nonoverlaps = (otherfeat for otherfeat in nonoverlaps if subkey(feat, otherfeat))
                # then calc dist for nonoverlaps
                if n:
                    nonoverlaps = list(nonoverlaps)
                    #print "nearsort",len(nonoverlaps)
                    for otherfeat in nearest(feat, nonoverlaps):
                        # if it gets this far it will be slow regardless of n,
                        # since all dists have to be calculated in order to sort them
                        matches.append(otherfeat)
                        if n and len(matches) >= n:
                            #print "ne",len(matches)
                            break
                else:
                    # means radius is only criteria,
                    # so join with all (within radius)
                    matches.extend(list(nonoverlaps))
                    #print "wt2",len(matches)

            # add
            if matches:
                for match in matches:
                    if clip:
                        geoj = clip(feat, match)
                    else:
                        geoj = feat.geometry
                    newrow = list(feat.row)
                    newrow += (match.row[i] for i in otheridx)
                    out.add_feature(newrow, geoj)
                
            elif keepall:
                # no matches
                newrow = list(feat.row)
                newrow += (None for i in otheridx)
                out.add_feature(newrow, feat.geometry)
                
        return out

    elif condition in ("intersects", "within", "contains", "crosses", "touches", "equals", "covers"):
        # prep geoms in other
        for otherfeat in other:
            if not otherfeat.geometry:
                continue
            otherfeat._shapely = otherfeat.get_shapely()

        # begin
        for feat in data.quick_overlap(other.bbox):

            #print feat

            if not feat.geometry:
                if keepall:
                    newrow = list(feat.row)
                    newrow += (None for i in otheridx)
                    out.add_feature(newrow, None)
                continue

            # match funcs
            geom = feat.get_shapely()
            if condition in ("intersects", "contains", "covers"):
                supergeom = supershapely(geom)
                matchtest = getattr(supergeom, condition)
            else:
                matchtest = getattr(geom, condition)

            # get spindex possibilities
            matches = (otherfeat for otherfeat in other.quick_overlap(feat.bbox))
            # filter by subkey
            if subkey:
                matches = (otherfeat for otherfeat in matches if subkey(feat, otherfeat))
            # test spatial
            matches = [otherfeat for otherfeat in matches if matchtest(otherfeat._shapely)]
            if matches:
                for match in matches:
                    if clip:
                        geoj = clip(feat, match)
                    else:
                        geoj = feat.geometry
                    newrow = list(feat.row)
                    newrow += (match.row[i] for i in otheridx)
                    out.add_feature(newrow, geoj)

            elif keepall:
                # no matches
                newrow = list(feat.row)
                newrow += (None for i in otheridx)
                out.add_feature(newrow, feat.geometry)
                
        return out

    elif condition in ("disjoint",):
        # prep geoms in other
        for otherfeat in other:
            if not otherfeat.geometry:
                continue
            otherfeat._shapely = otherfeat.get_shapely()

        # begin
        for feat in data:

            # check empty geom
            if not feat.geometry:
                if keepall:
                    newrow = list(feat.row)
                    newrow += (None for i in otheridx)
                    out.add_feature(newrow, None)
                continue
            
            # first add those whose bboxes clearly dont overlap
            nonoverlaps = []
            for otherfeat in other.quick_disjoint(feat.bbox):
                if subkey and not subkey(feat,otherfeat):
                    continue
                nonoverlaps.append(otherfeat)

            # then check those that might overlap
            geom = feat.get_shapely()
            # get spindex possibilities
            closeones = (otherfeat for otherfeat in other.quick_overlap(feat.bbox))
            # filter by subkey
            if subkey:
                closeones = (otherfeat for otherfeat in closeones if subkey(feat, otherfeat))
            # test spatial
            closeones = [otherfeat for otherfeat in closeones if geom.disjoint(otherfeat._shapely)]

            # add
            matches = nonoverlaps + closeones
            if matches:
                for match in matches:
                    if clip:
                        geoj = clip(feat, match)
                    else:
                        geoj = feat.geometry
                    newrow = list(feat.row)
                    newrow += (match.row[i] for i in otheridx)
                    out.add_feature(newrow, geoj)

            elif keepall:
                # no matches
                newrow = list(feat.row)
                newrow += (None for i in otheridx)
                out.add_feature(newrow, feat.geometry)

        return out
    
    else:
        raise Exception("%s is not a valid join condition" % condition)









# File management

def split(data, key, breaks="unique", **kwargs):
    """
    Splits a vector data layer into multiple ones based on a key which can be
    a field name, a list of field names, or a function. The default is to
    create a split for each new unique occurance of the key value, but the
    breaks arg can also be set to the name of other classification algorithms
    or to a list of your own custom break values. The key, breaks, and kwargs
    follow the input and behavior of the ClassyPie package's split and unique
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

    import classypie as cp
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

def snap(data, otherdata, tolerance=0.0000001):
    """Snaps all vertexes from the features in one layer snap to the vertexes of features in another layer within a certain distance"""
    
    # default should be 0.001 meters (1 millimeter), ala ArcGIS
    # should be calculated based on crs

    # NOTSURE: for now, if multiple within tolerance, snaps first to furtherst away, then to next farthest, etc.
    # this means might be snapped back and forth multiple times, but at least the closest one will have the final say.

    if not hasattr(otherdata, "spindex"):
        otherdata.create_spatial_index()

    from shapely.ops import snap as _snap

    out = data.copy()
    for feat in out:
        shp = feat.get_shapely()
        buff = shp.buffer(tolerance)
        withindist = (otherfeat.get_shapely() for otherfeat in otherdata.quick_overlap(buff.bounds))
        withindist = (othershp for othershp in withindist if buff.intersects(othershp))
        withindist = ((othershp,shp.distance(othershp)) for othershp in withindist)
        for othershp,dist in sorted(withindist, key=lambda(shp,dist): dist, reverse=True):
            print "snap"
            shp = _snap(shp, othershp, tolerance)
        feat.geometry = shp.__geo_interface__
        
    return out









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

def buffer(data, dist, join_style="round", cap_style="round", mitre_limit=1.0, geodetic=False, resolution=None):
    """
    Buffering the data by a positive distance grows the geometry,
    while a negative distance shrinks it. Distance units should be given in
    units of the data's coordinate reference system. 

    Distance is an expression written in Python syntax, where it is possible
    to access the attributes of each feature by writing: feat['fieldname'].
    """
    # get distance func
    if hasattr(dist, "__call__"):
        distfunc = dist
    else:
        distfunc = lambda f: dist 

    # get buffer func
    if geodetic:
        # geodetic
        if data.type != None and data.type != "Point":
            raise Exception("Geodetic buffer only implemented for points")

        from ._helpers import geodetic_buffer
        kwargs = dict()
        if resolution:
            kwargs["resolution"] = resolution
        def bufferfunc(feat):
            geoj = feat.geometry
            distval = distfunc(feat)
            return geodetic_buffer(geoj, distval, **kwargs)

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
        if feat.geometry:
            buffered = bufferfunc(feat)
            new.add_feature(feat.row, buffered)
        
    # change data type to polygon
    new.type = "Polygon"
    return new

def cut(data, cutter):
    """
    Cuts apart a layer by the lines of another layer
    """

    # TODO: not sure if correct yet
    # NOTE: requires newest version of shapely

    from shapely.ops import split as _split

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

        cutgeoms = (cutfeat.get_shapely() for cutfeat in cutter.quick_overlap(feat.bbox))
        cutgeoms = (cutgeom for cutgeom in cutgeoms if cutgeom.intersects(geom))
        def flat(g):
            if hasattr(g, "geoms"):
                return g.geoms
            else:
                return [g]
        cutgeom = shapely.geom.MultiPolygon(sum((flat(g) for g in cutgeoms)))
        newgeom = _split(geom, cutgeom)

        # add feature
        outdata.add_feature(feat.row, newgeom.__geo_interface__)
        
    return outdata

def reproject(data, tocrs):
    """Reprojects from one crs to another"""
    import pyproj

    # get pycrs objs
    fromcrs = data.crs
    if not isinstance(tocrs, pycrs.CS):
        tocrs = pycrs.parse.from_unknown_text(tocrs)

    # create pyproj objs
    fromproj = pyproj.Proj(fromcrs.to_proj4())
    toproj = pyproj.Proj(tocrs.to_proj4())

    def _project(points):
        xs,ys = itertools.izip(*points)
        xs,ys = pyproj.transform(fromproj,
                                 toproj,
                                 xs, ys)
        newpoints = list(itertools.izip(xs, ys))
        return newpoints

    out = data.copy()
    out.crs = pycrs.parse.from_proj4(tocrs.to_proj4()) # separate copy
    
    for feat in out:
        feat.transform(_project)

    return out



