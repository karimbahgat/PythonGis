
import itertools, operator
from .data import *
from .manager import *

import PIL.Image, PIL.ImageMath, PIL.ImageStat
import math


# Zonal aggregation

##def zonal_statistics(zonaldata, valuedata, zonalband=0, valueband=0, outstat="mean"):
##    """
##    For each unique zone in "zonaldata", summarizes "valuedata" cells that overlap "zonaldata".
##    Which band to use must be specified for each.
##
##    The "outstat" statistics option can be one of: mean, median, max, min, stdev, var, count, or sum
##    """
##    # get nullvalues
##    nullzone = zonaldata.info.get("nodata_value")
##
##    # position value grid into zonal grid
##    (valuedata,valuemask) = valuedata.positioned(zonaldata.width, zonaldata.height,
##                                                 zonaldata.bbox)
##
##    # pick one image band for each
##    zonalimg = zonaldata.bands[zonalband].img
##    valueimg = valuedata.bands[valueband].img
##
##    # create output image, using nullzone as nullvalue
##    outimg = PIL.Image.new("F", zonalimg.size, nullzone)
##
##    # get stats for each unique value in zonal data
##    zonevalues = [val for count,val in zonalimg.getcolors()]
##    zonesdict = {}
##    for zoneval in zonevalues:
##        # exclude nullzone
##        if zoneval == nullzone: continue
##
##        # mask only the current zone
##        zonemask = zonalimg.point(lambda px: 1 if px == zoneval else 0, "1")
##        fullmask = PIL.Image.new("1", zonemask.size, 0)
##        # also exclude null values from calculations
##        fullmask.paste(zonemask, valuemask)
##
##        # retrieve stats
##        stats = PIL.ImageStat.Stat(valueimg, fullmask)
##        statsdict = {}
##        statsdict["min"],statsdict["max"] = stats.extrema[0]
##        for stattype in ("count","sum","mean","median","var","stddev"):
##            try: statsdict[stattype] = stats.__getattr__(stattype)[0]
##            except ZeroDivisionError: statsdict[stattype] = None
##        zonesdict[zoneval] = statsdict
##
##        # write chosen stat to outimg
##        outimg.paste(statsdict[outstat], (0,0), zonemask)
##
##    # make outimg to raster
##    outraster = Raster(image=outimg, **zonaldata.info)
##        
##    return zonesdict, outraster



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

def interpolate(pointdata, rasterdef, valuefield=None, algorithm="IDW", **kwargs):
    if algorithm.lower() == "idw":
        dsafda
        
    elif algorithm.lower() == "gauss":
        # create output raster
        raster = RasterData(**rasterdef)
        raster.add_band() # add empty band
        newband = raster.bands[0]
        
        # collect counts or sum field values
        for feat in pointdata:
            x,y = feat.geometry["coordinates"]
            px,py = raster.geo_to_cell(x,y)
            #print x,y,px,py
            val = feat[valuefield] if valuefield else 1
            oldval = newband.get(px,py).value
            if oldval != newband.nodataval:
                newband.set(px,py, oldval+val)

        #print newband.img.getextrema()
        #newband.img.point(lambda px: px*60).show()

        # apply gaussian filter
        # WONT WORK SINCE FILTERS ONLY WORK FOR L MODE
        ##        import PIL, PIL.ImageOps
        ##        print band.img.getextrema()
        ##        band.img = band.img.point(lambda px: px*51)
        ##        print band.img.getextrema()
        ##        band.img.show()
        ##        import PIL, PIL.ImageFilter
        ##        filt = PIL.ImageFilter.GaussianBlur() # TODO allow setting the radius
        ##        # hmm, filter doesnt work on I or F images. 
        ##        band.img = band.img.convert("L")
        ##        band.img = band.img.filter(filt)
        ##        print band.img.getextrema()

        # MANUAL GAUSS
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
                
        #print newband.img.getcolors()
        #print origband.img.getcolors()
        #print id(newband),id(raster.bands[0]),id(origband)
                
        #maxval = newband.img.getextrema()[1]
        #maxfact = 1/float(maxval)*255
        #newband.img.point(lambda px: px*maxfact).show()

    elif algorithm.lower() == "circular":
        # create output raster
        raster = RasterData(**rasterdef)
        raster.add_band() # add empty band
        band = raster.bands[0]

        # calculate for each cell
        if not hasattr(pointdata, "spindex"):
            pointdata.create_spatial_index()
        raster.convert("F") # output will be floats
        if not "radius" in kwargs:
            raise Exception("Radius must be set for linear method")
        rad = float(kwargs["radius"])
        c = None
        for cell in band:
            
            if c != cell.row:
                print cell.row
                c = cell.row
                
            px,py = cell.col,cell.row
            x,y = raster.cell_to_geo(px,py)
            #sumval = 0.0
            
            # NOTE: need to group all values per pixel,
            # ...then run user specified agg function
            weights = []
            for feat in pointdata.quick_overlap([x-rad,y-rad,
                                                 x+rad,y+rad]):
                fx,fy = feat.geometry["coordinates"] # assumes single point
                dist = math.sqrt((fx-x)**2 + (fy-y)**2)
                if dist <= rad:
                    weight = feat[valuefield] if valuefield else 1
                    #sumval += weight * (1 - (dist / rad))
                    weights.append(weight * (1 - (dist / rad)))
            #if sumval > 0:
            #    cell.value = sumval
            if weights:
                cell.value = sum(weights)/float(len(weights))
                
        #maxval = band.img.getextrema()[1]
        #maxfact = 1/float(maxval)*255
        #band.img.point(lambda px: px*maxfact).show()

    elif algorithm.lower() == "boxsum":
        # http://stackoverflow.com/questions/6652671/efficient-method-of-calculating-density-of-irregularly-spaced-points
        # ...
        pass

    elif algorithm.lower() == "spline":
        # see C scripts at http://davis.wpi.edu/~matt/courses/morph/2d.htm
        # looks simple enough
        # ...
        pass

    return raster

def heatmap(**kwargs):
    # some links
    #http://docs.scipy.org/doc/scipy-0.16.0/reference/generated/scipy.interpolate.RegularGridInterpolator.html
    #https://github.com/JohannesBuchner/regulargrid
    #http://stackoverflow.com/questions/24978052/interpolation-over-regular-grid-in-python
    #http://www.qgistutorials.com/en/docs/creating_heatmaps.html

    #see especially: http://resources.arcgis.com/en/help/main/10.1/index.html#//009z0000000v000000
    
    return interpolate(**kwargs)

def densitymap():
    # only difference being no value field contributes to heat
    pass






# Distance Analysis

def distance(vectordata, **rasterdef):
    # aka proximity raster
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






