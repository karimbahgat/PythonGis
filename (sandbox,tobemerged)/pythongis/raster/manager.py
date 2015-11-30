import PIL, PIL.Image
import pyagg


def resample(raster, width=None, height=None, cellwidth=None, cellheight=None):
    raster = raster.copy()
    del raster._cached_mask # so that mask can be recreated for changed raster

    print "copied",raster.bbox

    if width and height:
        # calculate new cell dimensions based on the new raster size
        widthfactor = raster.width / float(width)
        heightfactor = raster.height / float(height)
        oldcellwidth, oldcellheight = raster.info["cellwidth"], raster.info["cellheight"]
        newcellwidth, newcellheight = oldcellwidth * widthfactor, oldcellheight * heightfactor
        
        # resample each grid
        for grid in raster:
            grid.img = grid.img.resize((width, height), PIL.Image.NEAREST)
            # update cells access
            grid.cells = grid.img.load()
            
        # remember new celldimensions
        raster.info["cellwidth"] = newcellwidth
        raster.info["cellheight"] = newcellheight # reverse bc opposite image and geo yaxis
        raster.update_geotransform()
        return raster
    
    elif cellwidth and cellheight:
        # calculate new raster size based on the new cell dimensions
        widthfactor = raster.info["cellwidth"] / float(cellwidth)
        heightfactor = raster.info["cellheight"] / float(cellheight)
        oldwidth, oldheight = raster.width, raster.height
        newwidth, newheight = int(round(oldwidth * widthfactor)), int(round(oldheight * heightfactor))
        print raster.info
        if newwidth < 0: newwidth *= -1
        if newheight < 0: newheight *= -1
        
        # resample each grid
        print newwidth,newheight
        for grid in raster:
            grid.img = grid.img.resize((newwidth, newheight), PIL.Image.NEAREST)
            print grid.img
            # update cells access
            grid.cells = grid.img.load()
            
        # remember new celldimensions
        raster.info["cellwidth"] = cellwidth
        raster.info["cellheight"] = cellheight # reverse bc opposite image and geo yaxis
        raster.update_geotransform()
        print "blii",raster.info,raster.width,raster.height,raster.bbox
        return raster
    
    else:
        raise Exception("To rescale raster, either width and height or cellwidth and cellheight must be specified.")


def combine_bands():
    pass


def split_bands():
    pass

def align_rasters(*rasters):
    for rast in rasters: print rast.bbox
    # resample to same dimensions of first raster (arbitrary)
    #rasters = [resample(rast, width=rasters[0].width, height=rasters[0].height)
    #           for rast in rasters]
    
    # get coord bbox containing all rasters
    print rasters
    for rast in rasters: print rast.bbox
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
        #rast.grids[0].img.save("C:/Users/kimo/Desktop/realpos.png")
        coordbbox = [xleft,ytop,xright,ybottom]
        print coordbbox
        positioned,mask = rast.positioned(reqwidth, reqheight, coordbbox)
        aligned.append((positioned,mask))
    return aligned

def mosaic(*rasters, **kwargs):
    """
    Mosaic rasters covering different areas together into one file.
    Parts of the rasters may overlap each other, in which case one must
    specify how to choose the final value. 
    """
    # use cellsize of first raster if not manually assigned
##    firstraster = rasters[0]
##    cellwidth = kwargs.get("cellwidth")
##    cellheight = kwargs.get("cellheight")
##    if not (cellwidth and cellheight):
##        cellwidth = firstraster.info["cellwidth"]
##        cellheight = firstraster.info["cellheight"]
    
    # align first band of all rasters and resample to output
    aligned = align_rasters(*rasters)
    #aligned = [resample(rast, cellwidth=cellwidth, cellheight=cellheight)
    #           for rast in aligned]
    firstalign,firstmask = aligned[0]
    merged = firstalign.copy()
    for rast,mask in aligned[1:]:
        merged.grids[0].img.paste(rast.grids[0].img, (0,0), mask)

    return merged
    
##    firstraster = rasters[0]
##    
##    # use cellsize of first raster if not manually assigned
##    if not (cellwidth and cellheight):
##        cellwidth = firstraster.info["cellwidth"]
##        cellheight = firstraster.info["cellheight"]
##        
##    # compute the required output coordinate bbox from all raster's coordinate bboxes
##    bboxes = [raster.bbox for raster in rasters]
##    xmins,ymins,xmaxs,ymaxs = zip(*bboxes)
##    bbox = min(xmins), min(ymins), max(xmaxs), max(ymaxs)
##
##    # create a new blank image big enough to encompass the coord bbox of all input rasters
##    rasterwidth = int(round((bbox[2]-bbox[0])/float(cellwidth)))
##    rasterheight = int(round((bbox[3]-bbox[1])/float(cellheight)))
##    merged = pyagg.new("F", rasterwidth, rasterheight)
##    merged.custom_space(*bbox)
##    
##    # add rasters to blank image
##    for raster in rasters:
##        # transform/bend image to its coordinate positions
##        warped = raster.warped()
##        
##        # resize raster to new cellsize
##        resized = resample(warped, cellwidth=cellwidth, cellheight=cellheight)
##        
##        # find coord of nw corner
##        nw = resized.cell_to_geo(0,0)
##
##        # find that coord's pixel location in larger output image
##        pasteloc = merged.geo_to_cell(*nw)
##        
##        # only take first grid to make them compatible
##        img = resized.grids[0].img
##        
##        # paste to pixel location of that coord
##        merged.paste(pasteloc, img)
##        #AND/OR consider overlapping pixel rule
##        #ie first(paste using original as mask),last(paste straight on top),
##        #mean(PIL blend with 0.5 alpha),min,or max(use a .eval function?)
##
##    # create raster from output image and return
##    # ...
##    # ...


def georeference(rasterdata, controlpointpairs):
    pass
    # change controlpoint pairs to degenerate rectangles
    # and send these to PIL mesh


def from_vector(vectordata, valuefield, cellwidth, cellheight, **options):
    # ie rasterize
    # calculate required raster size from cell dimensions
    vectorbbox = vectordata.bbox
    xmin,ymin,xmax,ymax = vectorbbox
    oldwidth, oldheight = xmax-xmin, ymax-ymin
    newwidth, newheight = oldwidth/float(cellwidth), oldheight/float(cellheight)
    newwidth, newheight = int(round(newwidth)), int(round(newheight))
    
    # simply create pyagg image with specified image size
    canvas = pyagg.Canvas(newwidth, newheight)
    
    # set the coordspace to vectordata bbox
    canvas.custom_space(*vectorbbox)
    
    # draw the vector data
    for feat in vectordata:
        geotype = feat.geometry["type"]
        # NOTE: NEED TO MAKE SURE IS NUMBER, AND PYAGG ONLY TAKES RGB VALID NRS
        # FIX...
        value = feat[valuefield]
        #   polygon, basic black fill, no outline
        if "Polygon" in geotype:
            canvas.draw_geojson(feat.geometry, fillcolor=(value,0,0), outlinecolor=None)
        #   line, 1 pixel line thickness
        elif "LineString" in geotype:
            canvas.draw_geojson(feat.geometry, fillcolor=(value,0,0), fillsize=1)
        #   point, 1 pixel square size
        elif "Point" in geotype:
            canvas.draw_geojson(feat.geometry, fillcolor=(value,0,0), fillsize=1)
            
    # create raster from the drawn image (only first band)
    img = canvas.get_image().split()[0]
    raster = pg.Raster(image=img, cellwidth=cellwidth, cellheight=cellheight,
                                         **options)
    return raster

def to_vector(raster, vectortype="point"):
    # create new vector data
    # for each cell,
    #   set polygon geom with the cell's coord bbox
    #   set row to the value of each grid at that cell location, eg [r,g,b]
    # OR...
    # (only for single band)
    # recursively follow neighbouring cells with same value
    #   collect coordinate for each cell with a different neighbour (edge cell)
    #   sort all coordinates as incr x and incr y, ie ccw
    #   add new polygon with sorted coords
    pass

def clip_keep(raster, clipdata):
    if isinstance(clipdata, pg.GeoTable):
        # rasterize vector data using same gridsize as main raster
        # create blank image
        # paste main raster onto blank image using rasterized as mask
        pass

    elif isinstance(clipdata, pg.Raster):
        # create blank image
        # paste raster onto blank image using clip raster as mask
        pass

def clip_exclude(data):
    # ...
    pass






