
from . import data
##from .. import raster
##from .. import vector

import PIL, PIL.Image, PIL.ImageDraw, PIL.ImagePath

##def align_rasters(*rasters):
##    "Used internally by other functions only, not by user"
##    # get coord bbox containing all rasters
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
##        coordbbox = [xleft,ytop,xright,ybottom]
##        positioned,mask = rast.positioned(reqwidth, reqheight, coordbbox)
##        aligned.append((positioned,mask))
##    return aligned

##def mosaic(*rasters):
##    """
##    Mosaic rasters covering different areas together into one file.
##    Parts of the rasters may overlap each other, in which case we use the value
##    from the last listed raster (the "last" overlap rule). 
##    """
##    # align all rasters, ie resampling to the same dimensions as the first raster
##    aligned = align_rasters(*rasters)
##    # copy the first raster and reset the cached mask for the new raster
##    firstalign,firstmask = aligned[0]
##    merged = firstalign.copy()
##    del merged._cached_mask
##    # paste onto each other, ie "last" overlap rule
##    for rast,mask in aligned[1:]:
##        merged.bands[0].img.paste(rast.bands[0].img, (0,0), mask)
##        
##    return merged

def reproject(raster, crs=None, algorithm="nearest", **rasterdef):
    
    algocode = {"nearest":PIL.Image.NEAREST,
                "bilinear":PIL.Image.BILINEAR,
                "bicubic":PIL.Image.BICUBIC,
                }[algorithm.lower()]

    if not crs:
        crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

    if crs != raster.crs:   # need pycrs to compare crs in a smarter way

        raise Exception("Conversion between crs not yet implemented")

        ##        # first, create target raster based on rasterdef
        ##        targetrast = data.RasterData(**rasterdef)
        ##        for band in raster:
        ##            targetrast.add_band(img=band.img)
        ##
        ##        # get target coordinates
        ##        lons = PIL.ImagePath.Path([targetrast.cell_to_geo(px,0) for px in range(targetrast.width)])
        ##        lats = PIL.ImagePath.Path([targetrast.cell_to_geo(0,py) for py in range(targetrast.height)])
        ##
        ##        # reproject coords using pyproj
        ##        for row,lat in enumerate(lats):
        ##            # convert crs coords
        ##            reproj = PIL.ImagePath.Path([pyproj.convert(lon,lat) for lon in lons])
        ##
        ##            # go from reprojected target coordinates and over to source pixels
        ##            sourcepixels = reproj.transform(raster.inv_affine)
        ##
        ##            # manually get and set the pixels using some algorithm
        ##            if algorithm == "nearest":
        ##                for sourceband,targetband in zip(raster,targetrast):
        ##                    for col,pixel in enumerate(sourcepixels):
        ##                        pixel = int(round(pixel[0])),int(round(pixel[1]))
        ##                        val = sourceband.get(*pixel)
        ##                        targetband.set(col,row,val)

    else:
        
        # same crs, so only needs to resample between affine transforms
        return resample(raster, algorithm, **rasterdef)

def resample(raster, algorithm="nearest", **rasterdef):

    algocode = {"nearest":PIL.Image.NEAREST,
                "bilinear":PIL.Image.BILINEAR,
                "bicubic":PIL.Image.BICUBIC,
                }[algorithm.lower()]
    
    # first, create target raster based on rasterdef
    targetrast = data.RasterData(mode=raster.mode, **rasterdef)
    
    # get coords of all 4 target corners
    coordspace_bbox = targetrast.bbox
    xleft,ytop,xright,ybottom = coordspace_bbox
    targetcorners = [(xleft,ytop), (xleft,ybottom), (xright,ybottom), (xright,ytop)]
    
    # find pixel locs of all these coords in the source raster
    targetcorners_pixels = [raster.geo_to_cell(*point, fraction=True) for point in targetcorners]

    # on raster, perform quad transform
    flattened = [xory for point in targetcorners_pixels for xory in point]

    # make mask over
    masktrans = raster.mask.transform((targetrast.width,targetrast.height),
                                        PIL.Image.QUAD,
                                        flattened,
                                        resample=algocode)

    for band in raster.bands:
        datatrans = band.img.transform((targetrast.width,targetrast.height),
                                        PIL.Image.QUAD,
                                        flattened,
                                        resample=algocode)
        #if mask
        if band.nodataval != None:
            datatrans.paste(band.nodataval, mask=masktrans)
            
        # store image
        targetrast.add_band(img=datatrans, nodataval=band.nodataval)

    return targetrast

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
                exterior = [tuple(p) for p in poly[0]]
                path = PIL.ImagePath.Path(exterior)
                #print list(path)[:10]
                path.transform((a,b,c,d,e,f))
                #print list(path)[:10]
                drawer.polygon(path, fill=1, outline=None)
                # holes
                if len(poly) > 1:
                    for hole in poly[1:]:
                        hole = [tuple(p) for p in hole]
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

def vectorize(rasterdata, **kwargs):
    # use PIL.ImageMorph.MorphOp() with an "edge" pattern.
    # ...
    pass

def crop(raster, bbox, resampling="nearest"):
    # either call resample directly, so just an alias
    # or find the pixels that are closest to the bbox and just do a normal image crop, meaning no resampling/changing of data
    pass

def clip(raster, clipdata, bbox=None):
    # TODO: HANDLE VARYING BAND NRS
    # TODO: ALSO HANDLE CLIP BY RASTER DATA
    # TODO: HANDLE FLIPPED COORDSYS AND/OR INTERPRETING VECTORDATA COORDSYS DIRECTION
    
    if True: #isinstance(clipdata, vector.data.VectorData):
        
        # rasterize vector data using same gridsize as main raster
        cellwidth,cellheight = raster.affine[0], raster.affine[4]
        mask = rasterize(clipdata, cellwidth, cellheight, bbox=bbox)

        # paste main raster onto blank image using rasterized as mask
        newwidth,newheight = mask.bands[0].img.size
        raster = raster.positioned(newwidth, newheight, mask.bbox)

        # make into raster
        outrast = data.RasterData(**raster.meta)  # not sure if correct

        # clip and add each band
        for band in raster.bands:
            
            # create blank image
            blank = PIL.Image.new(band.img.mode, (newwidth,newheight), band.nodataval)
            blank.paste(band.img, mask=mask.bands[0].img)
            pasted = blank

            outrast.add_band(img=pasted, nodataval=band.nodataval)

        return outrast

    elif isinstance(clipdata, raster.data.RasterData):
        # create blank image
        # paste raster onto blank image using clip raster as mask
        pass
