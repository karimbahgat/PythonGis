
import PIL, PIL.Image


def resample(raster, width=None, height=None, cellwidth=None, cellheight=None):
    """
    The raster stays in the same geographic location and coverage, but will
    have lower or higher cell resolution. 

    Either specify "width" and "height" as number of cells in each direction,
    or "cellwidth" and "cellheight" in geographic unit distances
    (defined by the raster's coordinate reference system). 
    """
    # copy the first raster and reset the cached mask for the new raster
    raster = raster.copy()
    del raster._cached_mask 

    if width and height:
        # calculate new cell dimensions based on the new raster size
        widthfactor = raster.width / float(width)
        heightfactor = raster.height / float(height)
        oldcellwidth, oldcellheight = raster.info["cellwidth"], raster.info["cellheight"]
        newcellwidth, newcellheight = oldcellwidth * widthfactor, oldcellheight * heightfactor
        
        # resample each grid
        for band in raster:
            band.img = band.img.resize((width, height), PIL.Image.NEAREST)
            # update cells access
            band.cells = band.img.load()
            
        # remember new celldimensions
        raster.info["cellwidth"] = newcellwidth
        raster.info["cellheight"] = newcellheight 
        raster.update_geotransform()
        return raster
    
    elif cellwidth and cellheight:
        # calculate new raster size based on the new cell dimensions
        widthfactor = raster.info["cellwidth"] / float(cellwidth)
        heightfactor = raster.info["cellheight"] / float(cellheight)
        oldwidth, oldheight = raster.width, raster.height
        newwidth, newheight = int(round(oldwidth * widthfactor)), int(round(oldheight * heightfactor))
        if newwidth < 0: newwidth *= -1
        if newheight < 0: newheight *= -1
        
        # resample each grid
        for band in raster:
            band.img = band.img.resize((newwidth, newheight), PIL.Image.NEAREST)
            # update cells access
            band.cells = band.img.load()
            
        # remember new celldimensions
        raster.info["cellwidth"] = cellwidth
        raster.info["cellheight"] = cellheight 
        raster.update_geotransform()
        return raster
    
    else:
        raise Exception("To rescale raster, either width and height or cellwidth and cellheight must be specified.")

def align_rasters(*rasters):
    "Used internally by other functions only, not by user"
    # get coord bbox containing all rasters
    xlefts,ytops,xrights,ybottoms = zip(*[rast.bbox for rast in rasters])
    if xlefts[0] < xrights[0]:
        xleft,xright = min(xlefts),max(xrights)
    else: xleft,xright = max(xlefts),min(xrights)
    if ytops[0] > ybottoms[0]:
        ytop,ybottom = max(ytops),min(ybottoms)
    else: ytop,ybottom = min(ytops),max(ybottoms)

    # get the required pixel dimensions (based on first raster, arbitrary)
    xs,ys = (xleft,xright),(ytop,ybottom)
    coordwidth,coordheight = max(xs)-min(xs), max(ys)-min(ys)
    rast = rasters[0]
    orig_xs,orig_ys = (rast.bbox[0],rast.bbox[2]),(rast.bbox[1],rast.bbox[3])
    orig_coordwidth,orig_coordheight = max(orig_xs)-min(orig_xs), max(orig_ys)-min(orig_ys)
    widthratio,heightratio = coordwidth/orig_coordwidth, coordheight/orig_coordheight
    reqwidth = int(round(rast.width*widthratio))
    reqheight = int(round(rast.height*heightratio))
    
    # position into same coordbbox
    aligned = []
    for rast in rasters:
        coordbbox = [xleft,ytop,xright,ybottom]
        positioned,mask = rast.positioned(reqwidth, reqheight, coordbbox)
        aligned.append((positioned,mask))
    return aligned

def mosaic(*rasters):
    """
    Mosaic rasters covering different areas together into one file.
    Parts of the rasters may overlap each other, in which case we use the value
    from the last listed raster (the "last" overlap rule). 
    """
    # align all rasters, ie resampling to the same dimensions as the first raster
    aligned = align_rasters(*rasters)
    # copy the first raster and reset the cached mask for the new raster
    firstalign,firstmask = aligned[0]
    merged = firstalign.copy()
    del merged._cached_mask
    # paste onto each other, ie "last" overlap rule
    for rast,mask in aligned[1:]:
        merged.bands[0].img.paste(rast.bands[0].img, (0,0), mask)
        
    return merged
    





