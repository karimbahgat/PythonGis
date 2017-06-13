
import itertools, operator
from .data import *
from . import manager

import PIL.Image, PIL.ImageMath, PIL.ImageStat, PIL.ImageMorph
import math


# Zonal aggregation

def zonal_statistics(zonaldata, valuedata, zonalband=0, valueband=0, outstat="mean", nodataval=-999):
    """
    For each unique zone in "zonaldata", summarizes "valuedata" cells that overlap "zonaldata".
    Which band to use must be specified for each.

    The "outstat" statistics option can be one of: mean, median, max, min, stdev, var, count, or sum

    For now, both must have same crs, no auto conversion done under the hood.
    """

    # handle zonaldata being vector type
    if not isinstance(zonaldata, RasterData):
        zonaldata = manager.rasterize(zonaldata, **valuedata.rasterdef)
    
    # resample value grid into zonal grid
    if zonaldata.affine != valuedata.affine:
        valuedata = manager.resample(valuedata, **zonaldata.rasterdef)

    # pick one band for each
    zonalband = zonaldata.bands[zonalband]
    valueband = valuedata.bands[valueband]

    # create output image, using nullzone as nullvalue
    georef = dict(width=valuedata.width, height=valuedata.height,
                  affine=valuedata.affine)
    outrast = RasterData(mode="float32", **georef)
    outrast.add_band(nodataval=nodataval)

    # get stats for each unique value in zonal data
    zonevalues = (val for count,val in zonalband.img.getcolors(zonaldata.width*zonaldata.height))
    zonesdict = {}
    zonalband.view()
    valueband.view()
    for zoneval in zonevalues:
        # exclude nullzone
        if zoneval == zonalband.nodataval: continue

        # mask valueband to only the current zone
        curzone = valueband.copy()
        print "copy"
        curzone.img.show()
        curzone.mask = zonalband.conditional("val != %s" % zoneval).img  # returns true everywhere, which is not correct..., maybe due to nodataval??? 
        print "cond",zoneval
        zonalband.conditional("val != %s" % zoneval).img.show()
        print "mask"
        curzone.img.show()        
        
        # also exclude null values from calculations
        curzone.mask = valueband.mask   # pastes additional nullvalues
        curzone._cached_mask = None    # force having to recreate the mask using the combined old and pasted nullvals
        print "mask2", curzone
        curzone.img.show()

        # retrieve stats
        stats = curzone.summarystats(outstat)
        zonesdict[zoneval] = stats

        # write chosen stat to outimg
        if stats[outstat] is None:
            stats[outstat] = nodataval
        outrast.bands[0].img.paste(stats[outstat], mask=curzone.mask)
        
    return zonesdict, outrast



# Raster math

def algebra(mathexpr, rasters):
    print rasters
    
    # align all to same affine
    rasters = (rast for rast in rasters)
    reference = next(rasters)
    def _aligned():
        yield reference
        for rast in rasters:
            if rast.affine != reference.affine:
                rast = manager.resample(rast, width=reference.width, height=reference.height, affine=reference.affine)
            yield rast

    # convert all nullvalues to zero before doing any math
    def _nulled():
        for rast in _aligned():
            for band in rast:
                # TODO: recode here somehow blanks out everything...
                #band.recode("val == %s"%band.nodataval, 0.0)
                pass
            yield rast
            
    # calculate math
    # basic math + - * / ** %
    # note: logical ops ~ & | ^ makes binary mask and return the pixel value where mask is valid
    # note: relational ops < > == != return only binary mask
    # note: other useful is min() and max(), equiv to (r1 < r2) | r2
    rastersdict = dict([("rast%i"%(i+1),rast.bands[0].img)#.convert("F"))
                        for i,rast in enumerate(_nulled())])
    img = PIL.ImageMath.eval(mathexpr, **rastersdict)

    # should maybe create a combined mask of nullvalues for all rasters
    # and filter away those nullcells from math result
    # ...

    # return result
    outraster = RasterData(image=img, **reference.meta)
    return outraster




# Interpolation

def interpolate(pointdata, rasterdef, valuefield=None, algorithm="idw", **kwargs):
    """Exact interpolation between point data values. Original values are kept intact"""

    # some links
    #http://docs.scipy.org/doc/scipy-0.16.0/reference/generated/scipy.interpolate.RegularGridInterpolator.html
    #https://github.com/JohannesBuchner/regulargrid
    #http://stackoverflow.com/questions/24978052/interpolation-over-regular-grid-in-python
    #http://www.qgistutorials.com/en/docs/creating_heatmaps.html
    #see especially: http://resources.arcgis.com/en/help/main/10.1/index.html#//009z0000000v000000

    # TODO: require aggfunc with exception...

    if not pointdata.type == "Point":
        raise Exception("Pointdata must be of type point")

    if rasterdef["mode"] == "1bit":
        raise Exception("Cannot do interpolation to a 1bit raster")

    algorithm = algorithm.lower()
    
    if algorithm == "idw":

        # create output raster
        raster = RasterData(**rasterdef)
        newband = raster.add_band() # add empty band

        # default options
        neighbours = kwargs.get("neighbours")
        sensitivity = kwargs.get("sensitivity")
        aggfunc = kwargs.get("aggfunc", "mean")
        
        # collect counts or sum field values
        from ..vector import sql
        def key(feat):
            x,y = feat.geometry["coordinates"]
            px,py = raster.geo_to_cell(x,y)
            return px,py
        def valfunc(feat):
            val = feat[valuefield] if valuefield else 1
            return val
        fieldmapping = [("aggval",valfunc,aggfunc)]
        points = dict()
        for (px,py),feats in itertools.groupby(pointdata, key=key):
            aggval = sql.aggreg(feats, fieldmapping)[0]
            if isinstance(aggval,(int,float)): # only consider numeric values, ignore missing etc
                points[(px,py)] = aggval

        # retrieve input options
        if neighbours == None:
            # TODO: not yet implemented
            neighbours = int(len(points)*0.10) #default neighbours is 10 percent of known points
        if sensitivity == None:
            sensitivity = 3 #same as power, ie that high sensitivity means much more effect from far away pointss

        # some precalcs
        senspow = (-sensitivity/2.0)

        # some defs
        def _calcvalue(gridx, gridy, points):
            weighted_values_sum = 0.0
            sum_of_weights = 0.0
            for (px,py),pval in points.items():
                weight = ((gridx-px)**2 + (gridy-py)**2)**senspow
                sum_of_weights += weight
                weighted_values_sum += weight * pval
            return weighted_values_sum / sum_of_weights

        # calculate values
        for gridy in range(raster.height):
            for gridx in range(raster.width):
                newval = points.get((gridx,gridy))
                if newval != None:
                    # gridxy to calculate is exact same as one of the point xy, so just use same value
                    pass
                else:
                    # main calc
                    newval = _calcvalue(gridx, gridy, points)
                newband.set(gridx,gridy,newval)

    elif algorithm == "spline":
        # see C scripts at http://davis.wpi.edu/~matt/courses/morph/2d.htm
        # looks simple enough
        # ...

        raise Exception("Not yet implemented")

    elif algorithm == "kdtree":
        # https://github.com/stefankoegl/kdtree
        # http://rosettacode.org/wiki/K-d_tree
        
        raise Exception("Not yet implemented")

    elif algorithm == "kriging":
        # ...?
        
        raise Exception("Not yet implemented")

    else:
        raise Exception("Not a valid interpolation algorithm")

    return raster

def smooth(pointdata, rasterdef, valuefield=None, algorithm="radial", **kwargs):
    """
    Bins and aggregates point data values, followed by simple value smearing to produce a smooth surface raster.
    Different from interpolation in that the new values do not exactly pass through the original values.
    Aka heatmap in the proper sense. 
    """

    if not pointdata.type == "Point":
        raise Exception("Pointdata must be of type point")

    if rasterdef["mode"] == "1bit":
        raise Exception("Cannot do interpolation to a 1bit raster")

    algorithm = algorithm.lower()

    if algorithm == "radial":
        # create output raster
        raster = RasterData(**rasterdef)
        raster.add_band() # add empty band
        band = raster.bands[0]

        # calculate for each cell
        if not hasattr(pointdata, "spindex"):
            pointdata.create_spatial_index()
        raster.convert("float32") # output will be floats
        if not "radius" in kwargs:
            raise Exception("Radius must be set for 'radial' method")
        rad = float(kwargs["radius"])
        c = None
        for cell in band:
            
            #if c != cell.row:
            #    print cell.row
            #    c = cell.row
                
            px,py = cell.col,cell.row
            x,y = raster.cell_to_geo(px,py)
            
            def weights():
                for feat in pointdata.quick_overlap([x-rad,y-rad,
                                                     x+rad,y+rad]):
                    fx,fy = feat.geometry["coordinates"] # assumes single point
                    dist = math.sqrt((fx-x)**2 + (fy-y)**2)
                    if dist <= rad:
                        weight = feat[valuefield] if valuefield else 1
                        yield weight * (1 - (dist / rad))

            from ..vector import sql
            valfunc = lambda(v): v
            aggfunc = kwargs.get("aggfunc", "sum")
            fieldmapping = [("aggval",valfunc,aggfunc)]
            aggval = sql.aggreg(weights(), fieldmapping)[0]
        
            if aggval or aggval == 0:
                cell.value = aggval

    elif algorithm == "gauss":
        # create output raster
        raster = RasterData(**rasterdef)
        raster.add_band() # add empty band
        newband = raster.bands[0]
        
        # collect counts or sum field values
        from ..vector import sql
        def key(feat):
            x,y = feat.geometry["coordinates"]
            px,py = raster.geo_to_cell(x,y)
            return px,py
        def valfunc(feat):
            val = feat[valuefield] if valuefield else 1
            return val
        fieldmapping = [("aggval",valfunc,aggfunc)]
        for (px,py),feats in itertools.groupby(pointdata, key=key):
            aggval = sql.aggreg(feats, fieldmapping)
            newband.set(px,py, aggval)

        # apply gaussian filter

        if raster.mode.endswith("8"):
            # PIL gauss filter only work on L mode images
            
            import PIL, PIL.ImageOps, PIL.ImageFilter
            rad = kwargs.get("radius", 3)
            filt = PIL.ImageFilter.GaussianBlur(radius=rad)
            band.img = band.img.filter(filt)

        else:
            # Gauss calculation in pure Python
            # algorithm 1 from http://blog.ivank.net/fastest-gaussian-blur.html
            # TODO: implement much faster algorithm 4
            
            origband = newband.copy()
            raster.convert("float32") # output values will be floats
            rad = kwargs.get("radius", 3)
            rs = int(rad*2.57+1) # significant radius
            
            # some precalcs
            rr2 = 2*rad*rad
            prr2 = float(math.pi*2*rad*rad)
            exp = math.exp
            for i in range(raster.height):
                #print i
                for j in range(raster.width):
                    val = 0.0
                    wsum = 0.0
                    for iy in range(i-rs, i+rs+1):
                        for ix in range(j-rs, j+rs+1):
                            x = min([raster.width-1, max([0,ix])])
                            y = min([raster.height-1, max([0,iy])])
                            dsq = (ix-j)*(ix-j)+(iy-i)*(iy-i)
                            weight = exp(-dsq/rr2) / prr2
                            val += origband.get(x,y).value * weight
                            wsum += weight
                    newval = val/wsum
                    #print j,i,newval
                    newband.set(j,i, newval)

    elif algorithm == "box":
        # http://stackoverflow.com/questions/6652671/efficient-method-of-calculating-density-of-irregularly-spaced-points
        # ...
        pass

    else:
        raise Exception("Not a valid smoothing algorithm")

    return raster

def density(pointdata, rasterdef, algorithm="radial", **kwargs):
    """Creates a raster of the density of points, ie the frequency of their occurance
    without thinking about the values of each point. Same as using the smooth function
    without setting the valuefield."""
    
    # only difference being no value field contributes to heat
    # TODO: allow density of linear and polygon features too,
    # maybe by counting nearby features
    
    return smooth(pointdata, rasterdef, valuefield=None, algorithm=algorithm, **kwargs)






# Distance Analysis

def distance(data, **rasterdef):
    """Calculates raster of distances to nearest feature in data"""
    # TODO: allow max dist limit
    if isinstance(data, RasterData):
        raise NotImplementedError("Distance tool requires vector data")

    from shapely.geometry import Point, MultiPoint, LineString, asShape

    outrast = RasterData(mode="float32", **rasterdef)
    outband = outrast.add_band() # make sure all values are set to 0 dist at outset

    fillband = manager.rasterize(data, **rasterdef).bands[0]

    # ALT1: each pixel to each feat
    # TODO: this approach is super slow...

##    geoms = [feat.get_shapely() for feat in data]
##    for cell in fillband:
##        if cell.value == 0:
##            # only calculate where vector is absent
##            #print "calc..."
##            point = Point(cell.x,cell.y) #asShape(cell.point)
##            dist = point.distance(geoms[0]) #min((point.distance(g) for g in geoms))
##            #print cell.col,cell.row,dist
##            outband.set(cell.col, cell.row, dist)
##        else:
##            pass #print "already set", cell.value

    # ALT2: each pixel to union
##    # TODO: this approach gets stuck...
##
##    import shapely
##    outline = shapely.ops.cascaded_union([feat.get_shapely() for feat in data])
##    for cell in fillband:
##        if cell.value == 0:
##            # only calculate where vector is absent
##            #print "calc..."
##            point = Point(cell.x,cell.y) 
##            dist = point.distance(outline) 
##            print cell.col,cell.row,dist
##            outband.set(cell.col, cell.row, dist)
##        else:
##            pass #print "already set", cell.value

    # ALT3: each pixel to each rasterized edge pixel
    # Pixel to pixel inspiration from: https://trac.osgeo.org/postgis/wiki/PostGIS_Raster_SoC_Idea_2012/Distance_Analysis_Tools/document
    # TODO: maybe shouldnt be outline points but outline line, to calc dist between points too?
    # TODO: current morphology approach gets crazy for really large rasters
    # maybe optimize by simplifying multiple points on straight line, and make into linestring
    
    #outlineband = manager.rasterize(data.convert.to_lines(), **rasterdef).bands[0]
##    outlinepixels = PIL.ImageMorph.MorphOp(op_name="edge").match(fillband.img)
##    print "outlinepixels",len(outlinepixels)
##    
##    outlinepoints = MultiPoint([outrast.cell_to_geo(*px) for px in outlinepixels])
##    
##    for cell in fillband:
##        if cell.value == 0:
##            # only calculate where vector is absent
##            point = Point(cell.x,cell.y)
##            dist = point.distance(outlinepoints)
##            outband.set(cell.col, cell.row, dist)

    # ALT4: each pixel to each rasterized edge pixel, with spindex
    
    #outlineband = manager.rasterize(data.convert.to_lines(), **rasterdef).bands[0]
    outlinepixels = PIL.ImageMorph.MorphOp(op_name="edge").match(fillband.img)
    print "outlinepixels",len(outlinepixels)

    import rtree
    spindex = rtree.index.Index()
    
    outlinepoints = [Point(*outrast.cell_to_geo(*px)) for px in outlinepixels]
    for i,p in enumerate(outlinepoints):
        bbox = p.bounds 
        spindex.insert(i, bbox)

    for cell in fillband:
        if cell.value == 0:
            # only calculate where vector is absent
            bbox = [cell.x, cell.y, cell.x, cell.y]
            nearestid = next(spindex.nearest(bbox, num_results=1))
            point = Point(cell.x,cell.y)
            dist = point.distance(outlinepoints[nearestid])
            outband.set(cell.col, cell.row, dist)

    # ALT5: each pixel to reconstructed linestring of rasterized edge pixels, superfast if can reconstruct
##    outlinepixels = PIL.ImageMorph.MorphOp(op_name="edge").match(fillband.img)
##    
##    # TODO: reconstruct linestring from outlinepixels...
##    outline = LineString([outrast.cell_to_geo(*px) for px in outlinepixels])
##
##    # TODO: simplify linestring...
####    print "outlinepixels",len(outlinepixels)
####    simplified = PIL.ImagePath.Path(outlinepixels)
####    simplified.compact(2) # 2 px    
####    outlinepixels = simplified.tolist()
####    print "simplified",len(outlinepixels)
##    
##    for cell in fillband:
##        if cell.value == 0:
##            # only calculate where vector is absent
##            point = Point(cell.x,cell.y)
##            dist = point.distance(outline)
##            outband.set(cell.col, cell.row, dist)

    # ALT6: incremental neighbour growth check overlap
    # ie
    #im = fillband.img
    #for _ in range(32):
    #    count,im = PIL.ImageMorph.MorphOp(op_name="erosion4").apply(im)
    #im.show()
    # ...

    return outrast






# Morphology

def morphology(raster, selection, pattern, bandnum=0):
    """
    General purpose morphology pattern operations, returning binary raster.
    Selection is the conditional expression to be interpreted as on-values. 
    Valid patterns include "edge", "dilation", "erosion", and
    manual input as expected by PIL.ImageMorph.
    """
    premask = raster.mask
    cond = raster.bands[bandnum].conditional(selection)
    count,im = PIL.ImageMorph.MorphOp(op_name=pattern).apply(cond.img)
    out = RasterData(image=im, **raster.rasterdef)
    out.mask = premask
    return out
    






# Path Analysis

def least_cost_path(point1, point2, **options):
    # use https://github.com/elemel/python-astar
    # maybe also: https://www.codeproject.com/articles/9040/maze-solver-shortest-path-finder
    pass





# Terrain Analysis

def viewshed(point, direction, height, raster, **kwargs):
    pass

def slope(raster):
    pass






