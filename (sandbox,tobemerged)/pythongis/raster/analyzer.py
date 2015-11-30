
import itertools, operator
from .data import *
from .manager import *

import PIL.Image, PIL.ImageMath, PIL.ImageStat, PIL.ImageChops



##def position_raster(raster, width, height, coordspace_bbox):
##    # GET COORDS OF ALL 4 VIEW SCREEN CORNERS
##    xleft,ytop,xright,ybottom = coordspace_bbox
##    viewcorners = [(xleft,ytop), (xleft,ybottom), (xright,ybottom), (xright,ytop)]
##    
##    # FIND PIXEL LOCS OF ALL THESE COORDS ON THE RASTER
##    viewcorners_pixels = [raster.geo_to_cell(*point, fraction=True) for point in viewcorners]
##    print viewcorners_pixels
##    print "---"
##
##    # ON RASTER, PERFORM QUAD TRANSFORM
##    #(FROM VIEW SCREEN COORD CORNERS IN PIXELS TO RASTER COORD CORNERS IN PIXELS)
##    flattened = [xory for point in viewcorners_pixels for xory in point]
##    newraster = raster.copy()
##    for grid in newraster.grids:
##        grid.img = grid.img.transform((width,height), PIL.Image.QUAD,
##                            flattened, resample=PIL.Image.NEAREST)
##        grid.cells = grid.img.load()
##        
##    return newraster
##
##def align_rasters(*rasters):
##    for rast in rasters: print rast.bbox
##    # resample to same dimensions of first raster (arbitrary)
##    #rasters = [resample(rast, width=rasters[0].width, height=rasters[0].height)
##    #           for rast in rasters]
##    
##    # get coord bbox containing all rasters
##    print rasters
##    for rast in rasters: print rast.bbox
##    xlefts,ytops,xrights,ybottoms = zip(*[rast.bbox for rast in rasters])
##    if xlefts[0] < xrights[0]:
##        xleft,xright = min(xlefts),max(xrights)
##    else: xleft,xright = max(xlefts),min(xrights)
##    if ytops[0] > ybottoms[0]:
##        ytop,ybottom = max(ytops),min(ybottoms)
##    else: ytop,ybottom = min(ytops),max(ybottoms)
##
##    # get the required pixel dimensions (based on first raster, arbitrary)
##    xs,ys = (xleft,xright),(ytop,ybottom)
##    coordwidth,coordheight = max(xs)-min(xs), max(ys)-min(ys)
##    rast = rasters[0]
##    orig_xs,orig_ys = (rast.bbox[0],rast.bbox[2]),(rast.bbox[1],rast.bbox[3])
##    orig_coordwidth,orig_coordheight = max(orig_xs)-min(orig_xs), max(orig_ys)-min(orig_ys)
##    widthratio,heightratio = coordwidth/orig_coordwidth, coordheight/orig_coordheight
##    reqwidth = int(round(rast.width*widthratio))
##    reqheight = int(round(rast.height*heightratio))
##    
##    # position into same coordbbox
##    aligned = []
##    for rast in rasters:
##        #rast.grids[0].img.save("C:/Users/kimo/Desktop/realpos.png")
##        coordbbox = [xleft,ytop,xright,ybottom]
##        print coordbbox
##        positioned = position_raster(rast, reqwidth, reqheight, coordbbox)
##        aligned.append(positioned)
##    return aligned
    



# Zonal aggregation

def zonal_statistics(zonaldata, valuedata, zonalband=0, valueband=0, outstat="mean"):
    #if isinstance(zonaldata, GeoTable):
        #rasterize
    #if isinstance(valuedata, GeoTable):
        #rasterize

    # get nullvalues
    nullzone = zonaldata.info.get("nodata_value")

    # position value grid into zonal grid
    #(zonaldata,zonalmask),(valuedata,valuemask) = align_rasters(zonaldata, valuedata)
    (valuedata,valuemask) = valuedata.positioned(zonaldata.width, zonaldata.height,
                                                 zonaldata.bbox)

    # pick one image band for each
    zonalimg = zonaldata.grids[zonalband].img
    #zonalimg.save(r"C:\Users\kimo\Desktop\zones.png")
    valueimg = valuedata.grids[valueband].img
    #valueimg.save(r"C:\Users\kimo\Desktop\values879.png")

    # create output image, using nullzone as nullvalue
    outimg = PIL.Image.new("F", zonalimg.size, nullzone)
    print 1234,zonalimg,outimg

    # get stats for each unique value in zonal data
    zonevalues = [val for count,val in zonalimg.getcolors()]
    zonesdict = {}
    for zoneval in zonevalues:
        # exclude nullzone
        if zoneval == nullzone: continue
        
        # simple
##        zonemask = PIL.Image.eval(zonalimg, lambda px: 255 if px == zoneval else 0)
##        stats = PIL.ImageStat.Stat(valueimg, zonemask)
##        zonemask.save("C:/Users/kimo/Desktop/zonemasks/zoneval%i.png"%zoneval)
        
        # mask only the current zone
        zonemask = zonalimg.point(lambda px: 1 if px == zoneval else 0, "1")
        fullmask = PIL.Image.new("1", zonemask.size, 0)
        # also exclude null values from calculations
        fullmask.paste(zonemask, valuemask)
        #fullmask.save("C:/Users/kimo/Desktop/zonemasks/zoneval%i.png"%zoneval)

        # retrieve stats
        stats = PIL.ImageStat.Stat(valueimg, fullmask)
        statsdict = {}
        statsdict["min"],statsdict["max"] = stats.extrema[0]
        for stattype in ("count","sum","mean","median","var","stddev"):
            try: statsdict[stattype] = stats.__getattr__(stattype)[0]
            except ZeroDivisionError: statsdict[stattype] = None
        zonesdict[zoneval] = statsdict

        # write chosen stat to outimg
        print outstat,statsdict[outstat]
        outimg.paste(statsdict[outstat], (0,0), zonemask)

    # make outimg to raster
    print 5678,outimg
    outraster = Raster(image=outimg, **zonaldata.info)
        
    return zonesdict, outraster
    




# Raster math

def math(mathexpr, rasters):
    print rasters
    rasters = align_rasters(*rasters)

    # convert all nullvalues to zero before doing any math
    for rast,mask in rasters:
        nodata = rast.info.get("nodata_value")
        for grid in rast:
            if nodata != None:
                grid.img = PIL.Image.eval(grid.img, lambda px: 0 if px == nodata else px)

    # calculate math
    # basic math + - * / ** %
    # note: logical ops ~ & | ^ makes binary mask and return the pixel value where mask is valid
    # note: relational ops < > == != return only binary mask
    # note: other useful is min() and max(), equiv to (r1 < r2) | r2
    rastersdict = dict([("raster%i"%(i+1),rast.grids[0].img)#.convert("F"))
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
    outraster = Raster(image=img, **firstrast.info)
    return outraster

##def logical(logicexpr, *rasters):
##    # use PIL.ImageChops: invert(ie ~),difference(ie positive a-b),logical_and(ie &),logical_or(ie |),logical_xor(ie ^)
##    # instead of lighter(ie >),darker(ie <), just use "min()" and "max()" inside ImageMath
##    # custom approach required for == != >= <= (or maybe just use "equal()" or "notequal()" inside ImageMath)
##    pass

def focal_statistics():
    # set value based on focal neighbourhood cell values
    # eg 3x3 or 5x5 cells
    # PIL.ImageFilter: min,max,mode(ie majority),median,rank
    # manual calculation required for sum,minority,range,std,variety
    pass
