
import itertools, operator
from .data import *
from .manager import *

import PIL.Image, PIL.ImageMath, PIL.ImageStat 



# Zonal aggregation

def zonal_statistics(zonaldata, valuedata, zonalband=0, valueband=0, outstat="mean"):
    """
    For each unique zone in "zonaldata", summarizes "valuedata" cells that overlap "zonaldata".
    Which band to use must be specified for each.

    The "outstat" statistics option can be one of: mean, median, max, min, stdev, var, count, or sum
    """
    # get nullvalues
    nullzone = zonaldata.info.get("nodata_value")

    # position value grid into zonal grid
    (valuedata,valuemask) = valuedata.positioned(zonaldata.width, zonaldata.height,
                                                 zonaldata.bbox)

    # pick one image band for each
    zonalimg = zonaldata.bands[zonalband].img
    valueimg = valuedata.bands[valueband].img

    # create output image, using nullzone as nullvalue
    outimg = PIL.Image.new("F", zonalimg.size, nullzone)

    # get stats for each unique value in zonal data
    zonevalues = [val for count,val in zonalimg.getcolors()]
    zonesdict = {}
    for zoneval in zonevalues:
        # exclude nullzone
        if zoneval == nullzone: continue

        # mask only the current zone
        zonemask = zonalimg.point(lambda px: 1 if px == zoneval else 0, "1")
        fullmask = PIL.Image.new("1", zonemask.size, 0)
        # also exclude null values from calculations
        fullmask.paste(zonemask, valuemask)

        # retrieve stats
        stats = PIL.ImageStat.Stat(valueimg, fullmask)
        statsdict = {}
        statsdict["min"],statsdict["max"] = stats.extrema[0]
        for stattype in ("count","sum","mean","median","var","stddev"):
            try: statsdict[stattype] = stats.__getattr__(stattype)[0]
            except ZeroDivisionError: statsdict[stattype] = None
        zonesdict[zoneval] = statsdict

        # write chosen stat to outimg
        outimg.paste(statsdict[outstat], (0,0), zonemask)

    # make outimg to raster
    outraster = Raster(image=outimg, **zonaldata.info)
        
    return zonesdict, outraster

# Raster math

def math(mathexpr, rasters):
    print rasters
    
    rasters = align_rasters(*rasters)

    # convert all nullvalues to zero before doing any math
    for rast,mask in rasters:
        nodata = rast.info.get("nodata_value")
        for band in rast:
            print 111,band.img
            if nodata != None:
                band.img = PIL.Image.eval(band.img, lambda px: 0 if px == nodata else px)

    # calculate math
    # basic math + - * / ** %
    # note: logical ops ~ & | ^ makes binary mask and return the pixel value where mask is valid
    # note: relational ops < > == != return only binary mask
    # note: other useful is min() and max(), equiv to (r1 < r2) | r2
    rastersdict = dict([("raster%i"%(i+1),rast.bands[0].img)#.convert("F"))
                        for i,(rast,mask) in enumerate(rasters)])
    print [img.mode for img in rastersdict.values()]
    #img = PIL.ImageChops.logical_xor(*rastersdict.values()[:2])
    img = PIL.ImageMath.eval(mathexpr, **rastersdict)

    # should maybe create a combined mask of nullvalues for all rasters
    # and filter away those nullcells from math result
    # ...

    # return result
    print img.mode
    firstrast,firstmask = rasters[0]
    outraster = RasterData(image=img, **firstrast.info)
    return outraster




