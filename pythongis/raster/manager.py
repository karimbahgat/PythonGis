
from . import data
##from .. import raster
##from .. import vector

import PIL, PIL.Image, PIL.ImageDraw, PIL.ImagePath

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
    
def rasterize(vectordata, cellwidth, cellheight, bbox=None, **options):
    # TODO: HANDLE FLIPPED COORDSYS AND/OR INTERPRETING VECTORDATA COORDSYS DIRECTION
    # calculate required raster size from cell dimensions
    if not bbox: bbox = vectordata.bbox
    xmin,ymin,xmax,ymax = bbox
    xwidth, yheight = xmax-xmin, ymax-ymin
    pxwidth, pxheight = xwidth/float(cellwidth), yheight/float(cellheight)
    pxwidth, pxheight = int(round(pxwidth)), int(round(pxheight))
    if pxwidth < 0: pxwidth *= -1
    if pxheight < 0: pxheight *= -1

    # create 1bit image with specified size
    img = PIL.Image.new("1", (pxwidth, pxheight), 0)
    drawer = PIL.ImageDraw.Draw(img)

    # set the coordspace to vectordata bbox
    xoffset,yoffset = xmin,ymax
    xscale,yscale = cellwidth,cellheight
    a,b,c = xscale,0,xoffset
    d,e,f = 0,yscale,yoffset
    # invert
    det = a*e - b*d
    if det != 0:
        idet = 1 / float(det)
        ra = e * idet
        rb = -b * idet
        rd = -d * idet
        re = a * idet
        a,b,c,d,e,f = (ra, rb, -c*ra - f*rb,
                       rd, re, -c*rd - f*re)

    # draw the vector data
    for feat in vectordata:
        geotype = feat.geometry["type"]

        # make all multis so can treat all same
        coords = feat.geometry["coordinates"]
        if not "Multi" in geotype:
            coords = [coords]

        # polygon, basic black fill, no outline
        if "Polygon" in geotype:
            for poly in coords:
                # exterior
                exterior = poly[0]
                path = PIL.ImagePath.Path(exterior)
                #print list(path)[:10]
                path.transform((a,b,c,d,e,f))
                #print list(path)[:10]
                drawer.polygon(path, fill=1, outline=None)
                # holes
                if len(poly) > 1:
                    for hole in poly[1:]:
                        path = PIL.ImagePath.Path(hole)
                        path.transform((a,b,c,d,e,f))
                        drawer.polygon(path, fill=0, outline=None)
                        
        # line, 1 pixel line thickness
        elif "LineString" in geotype:
            for line in coords:
                path = PIL.ImagePath.Path(line)
                path.transform((a,b,c,d,e,f))
                drawer.line(path, fill=1)
            
        # point, 1 pixel square size
        elif "Point" in geotype:
            path = PIL.ImagePath.Path(coords)
            path.transform((a,b,c,d,e,f))
            drawer.point(path, fill=1)

    # create raster from the drawn image    
    raster = data.RasterData(image=img, cellwidth=cellwidth, cellheight=cellheight,
                               xy_cell=(0,0), xy_geo=(xmin,ymax), **options)
    return raster




    # OLD BELOW
##
##    # simply create pyagg image with specified image size
##    canvas = pyagg.Canvas(newwidth, newheight)
##    
##    # set the coordspace to vectordata bbox
##    canvas.custom_space(*vectorbbox)
##    
##    # draw the vector data
##    for feat in vectordata:
##        geotype = feat.geometry["type"]
##        # NOTE: NEED TO MAKE SURE IS NUMBER, AND PYAGG ONLY TAKES RGB VALID NRS
##        # FIX...
##        value = feat[valuefield]
##        #   polygon, basic black fill, no outline
##        if "Polygon" in geotype:
##            canvas.draw_geojson(feat.geometry, fillcolor=(value,0,0), outlinecolor=None)
##        #   line, 1 pixel line thickness
##        elif "LineString" in geotype:
##            canvas.draw_geojson(feat.geometry, fillcolor=(value,0,0), fillsize=1)
##        #   point, 1 pixel square size
##        elif "Point" in geotype:
##            canvas.draw_geojson(feat.geometry, fillcolor=(value,0,0), fillsize=1)
##            
##    # create raster from the drawn image (only first band)
##    img = canvas.get_image().split()[0]
##    raster = pg.Raster(image=img, cellwidth=cellwidth, cellheight=cellheight,
##                                         **options)
##    return raster




def clip(raster, clipdata, bbox=None):
    # TODO: ALSO HANDLE CLIP BY RASTER DATA
    # TODO: HANDLE FLIPPED COORDSYS AND/OR INTERPRETING VECTORDATA COORDSYS DIRECTION
    
    if True: #isinstance(clipdata, vector.data.VectorData):
        # rasterize vector data using same gridsize as main raster

        #print "orig",raster.info
        #raster.bands[0].img.save("orig.png")
        
        mask = rasterize(clipdata, raster.info["cellwidth"], raster.info["cellheight"], bbox=bbox)

        #print "mask", mask.bands[0].img, mask.info
        #mask.bands[0].img.save("mask.png")
        
        # create blank image
        newwidth,newheight = mask.bands[0].img.size
        blank = PIL.Image.new(raster.bands[0].img.mode, (newwidth,newheight))

        #print "blank",blank

        # paste main raster onto blank image using rasterized as mask
        raster,_posmask = raster.positioned(newwidth, newheight, mask.bbox)

        #raster.bands[0].img.save("positioned.png")
        #print "positioned",raster.bands[0].img,raster.info

        blank.paste(raster.bands[0].img, (0,0), mask.bands[0].img)
        pasted = blank

        #print pasted
        #pasted.save("testclip.png")

        # make into raster
        outrast = data.RasterData(image=pasted, **raster.info)
        return outrast

    elif isinstance(clipdata, raster.data.RasterData):
        # create blank image
        # paste raster onto blank image using clip raster as mask
        pass

def clip_nlights_version(raster, vector):
    import PIL, PIL.Image, PIL.ImageDraw
    orig = raster.bands[0].img
    xleft,ytop,xright,ybottom = vector.bbox
    pxleft,pytop = raster.geo_to_cell(xleft,ytop)
    pxright,pybottom = raster.geo_to_cell(xright,ybottom)
    cropped = orig.crop([pxleft,pybottom,pxright,pytop]) #ys are flipped
    #cropped.show()

    import pyagg
    mask = pyagg.Canvas(cropped.width, cropped.height)
    mask.custom_space(*vector.bbox)
    mask.draw_geojson(vector.get_shapely(), fillcolor=(255,0,0), outlinecolor=None)
    #mask.view()

    clipped = PIL.Image.new("LA", cropped.size)
    clipped.paste(cropped, (0,0)) #, mask.img.convert("1"))
    #clipped.show()

    return clipped  # PIL image, but should be another RasterData
    
    ##    import pyagg
    ##    orig = pyagg.canvas.from_image(raster.bands[0].img)
    ##    orig.geographic_space()
    ##    cropped = orig.zoom_bbox(vector.bbox)
    ##    cropped.view()
        
    ##    mask = pyagg.Canvas("%spx"%data.width, "%spx"%data.height)
    ##    mask.draw_geojson(vector)
    ##    pyagg

def render(raster):   # PUT INTO render.py
    # equalize and colorize
    canv = pyagg.canvas.from_image(raster.bands[0].img)
    canv.img = canv.img.convert("L")
    canv = canv.equalize()
    canv = pyagg.canvas.from_image(canv.img.convert("RGBA"))
    canv = canv.color_remap([(0,0,55),
                             (255,255,0)
                             ])

    # draw country outline
    x1,y1,x2,y2 = syria.bbox
    canv.custom_space(x1,y2,x2,y1)
    canv.draw_geojson(syria.get_shapely(), fillcolor=None, outlinecolor=(255,0,0), outlinewidth="5px")

    # title
    canv.percent_space()
    canv.draw_text(filename, xy=(50,5), fillcolor=(255,255,255))

    # yield
    return canv
