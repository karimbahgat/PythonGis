
import itertools, operator
from .data import *
from . import manager

import PIL.Image, PIL.ImageMath, PIL.ImageStat
import math


# Zonal aggregation

def zonal_statistics(zonaldata, valuedata, zonalband=0, valueband=0, outstat="mean"):
    """
    For each unique zone in "zonaldata", summarizes "valuedata" cells that overlap "zonaldata".
    Which band to use must be specified for each.

    The "outstat" statistics option can be one of: mean, median, max, min, stdev, var, count, or sum

    For now, both must have same crs, no auto conversion done under the hood.
    """

    # handle zonaldata being vector type
    if not isinstance(zonaldata, RasterData):
        zonaldata = manager.rasterize(zonaldata, **valuedata.meta)
    
    # resample value grid into zonal grid
    if zonaldata.affine != valuedata.affine:
        valuedata = manager.resample(valuedata, **zonaldata.meta)

    # pick one band for each
    zonalband = zonaldata.bands[zonalband]
    valueband = valuedata.bands[valueband]

    # create output image, using nullzone as nullvalue
    georef = dict(width=valueband.width, height=valueband.height,
                  affine=valueband.affine)
    outrast = Raster(mode="float32", **georef)
    outrast.add_band(nodataval=valueband.nodataval)

    # get stats for each unique value in zonal data
    zonevalues = (val for count,val in zonalband.img.getcolors(self.width*self.height))
    zonesdict = {}
    for zoneval in zonevalues:
        # exclude nullzone
        if zoneval == zonalband.nodataval: continue

        # mask to only the current zone
        curzone = zonalband.copy()
        curzone.mask = curzone.conditional("val != %s" % zoneval).img
        
        # also exclude null values from calculations
        curzone.mask = valueband.mask   # pastes additional nullvalues
        del curzone._cached_mask    # force having to recreate the mask using the combined old and pasted nullvals

        # retrieve stats
        stats = curzone.summarystats(outstat)
        zonesdict[zoneval] = stats

        # write chosen stat to outimg
        outrast.bands[0].img.paste(statsdict[outstat], mask=curzone.mask)
        
    return zonesdict, outrast



# Raster math

##def raster_math(mathexpr, rasters):
##    print rasters
##    
##    rasters = align_rasters(*rasters)
##
##    # convert all nullvalues to zero before doing any math
##    for rast,mask in rasters:
##        nodata = rast.info.get("nodata_value")
##        for band in rast:
##            print 111,band.img
##            if nodata != None:
##                band.img = PIL.Image.eval(band.img, lambda px: 0 if px == nodata else px)
##
##    # calculate math
##    # basic math + - * / ** %
##    # note: logical ops ~ & | ^ makes binary mask and return the pixel value where mask is valid
##    # note: relational ops < > == != return only binary mask
##    # note: other useful is min() and max(), equiv to (r1 < r2) | r2
##    rastersdict = dict([("raster%i"%(i+1),rast.bands[0].img)#.convert("F"))
##                        for i,(rast,mask) in enumerate(rasters)])
##    print [img.mode for img in rastersdict.values()]
##    #img = PIL.ImageChops.logical_xor(*rastersdict.values()[:2])
##    img = PIL.ImageMath.eval(mathexpr, **rastersdict)
##
##    # should maybe create a combined mask of nullvalues for all rasters
##    # and filter away those nullcells from math result
##    # ...
##
##    # return result
##    print img.mode
##    firstrast,firstmask = rasters[0]
##    outraster = RasterData(image=img, **firstrast.info)
##    return outraster




# Interpolation

def interpolate(pointdata, rasterdef, valuefield=None, algorithm="idw", **kwargs):
    """Interpolation between point data values. Bins and aggregates point data
    values, followed by simple value smearing to produce a smooth surface raster"""

    # some links
    #http://docs.scipy.org/doc/scipy-0.16.0/reference/generated/scipy.interpolate.RegularGridInterpolator.html
    #https://github.com/JohannesBuchner/regulargrid
    #http://stackoverflow.com/questions/24978052/interpolation-over-regular-grid-in-python
    #http://www.qgistutorials.com/en/docs/creating_heatmaps.html
    #see especially: http://resources.arcgis.com/en/help/main/10.1/index.html#//009z0000000v000000

    if rasterdef["mode"] == "1bit":
        raise Exception("Cannot do interpolation to a 1bit raster")

    algorithm = algorithm.lower()
    
    if algorithm == "idw":

        raise Exception("Not yet implemented")

        ##        raster = RasterData(**rasterdef)
        ##
        ##        neighbours = kwargs.get("neighbours")
        ##        sensitivity = kwargs.get("sensitivity")
        ##        gridxs = (raster.cell_to_geo(px,0) for px in range(raster.width))
        ##        gridys = (raster.cell_to_geo(0,py) for py in range(raster.height))
        ##
        ##        #retrieve input options
        ##        if neighbours == None:
        ##            # TODO: not yet implemented
        ##            neighbours = int(len(points)*0.10) #default neighbours is 10 percent of known points
        ##        if sensitivity == None:
        ##            sensitivity = 3 #same as power, ie that high sensitivity means much more effect from far away pointss
        ##
        ##        # some precalcs
        ##        senspow = (-sensitivity/2.0)
        ##        
        ##        #some defs
        ##        def _calcvalue(gridx, gridy, points):
        ##            weighted_values_sum = 0.0
        ##            sum_of_weights = 0.0
        ##            for px,py,pval in points:
        ##                weight = ((gridx-px)**2 + (gridy-py)**2)**senspow
        ##                sum_of_weights += weight
        ##                weighted_values_sum += weight * pval
        ##            return weighted_values_sum / sum_of_weights
        ##        
        ##        # calculate values
        ##        for gridy in gridys:
        ##            newrow = []
        ##            for gridx in gridxs:
        ##                try:
        ##                    # main calc
        ##                    newval = _calcvalue(gridx, gridy, points)
        ##                except:
        ##                    # gridxy to calculate is exact same as one of the point xy, so just use same value
        ##                    newval = next(pval for px,py,pval in points if gridx == px and gridy == py) 
        ##                newrow.append(newval)
        ##
        ##        # finish off
        ##        # ...

    elif algorithm == "kdtree":
        # https://github.com/stefankoegl/kdtree
        # http://rosettacode.org/wiki/K-d_tree
        
        raise Exception("Not yet implemented")
        
    elif algorithm == "spline":
        # see C scripts at http://davis.wpi.edu/~matt/courses/morph/2d.htm
        # looks simple enough
        # ...

        raise Exception("Not yet implemented")

    elif algorithm == "kriging":
        # ...?
        
        raise Exception("Not yet implemented")

    elif algorithm == "radial":
        # create output raster
        raster = RasterData(**rasterdef)
        raster.add_band() # add empty band
        band = raster.bands[0]

        # calculate for each cell
        if not hasattr(pointdata, "spindex"):
            pointdata.create_spatial_index()
        raster.convert("F") # output will be floats
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
            fieldmapping = [("aggval",valfunc,aggfunc)]
            aggval = sql.aggreg(weights, fieldmapping)
        
            if aggval != None:
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
            raster.convert("F") # output values will be floats
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

    return raster

def density(pointdata, rasterdef, algorithm="radial", **kwargs):
    """Creates a raster of the density of points, ie the frequency of their occurance
    without thinking about the values of each point. Same as using the interpolate method
    without setting the valuefield."""
    
    # only difference being no value field contributes to heat
    # TODO: allow density of linear and polygon features too,
    # maybe by counting nearby features
    
    return interpolate(pointdata, rasterdef, valuefield=None, algorithm=algorithm, **kwargs)






# Distance Analysis

def proximity(vectordata, **rasterdef):
    # aka showing distances to nearest feature
    pass






# Path Analysis

def least_cost_path(point1, point2, **options):
    # use https://github.com/elemel/python-astar
    pass





# Terrain Analysis

def viewshed(point, direction, height, raster, **kwargs):
    pass

def slope(raster):
    pass






