
from . import data
##from .. import raster
##from .. import vector

import PIL, PIL.Image, PIL.ImageDraw, PIL.ImagePath

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

def morph(raster, gcp):
    # aka georeference
    # morph or smudge a raster in arbitrary directions based on a set of controlpoints
    # default algorithm is splines, maybe also polynomyal
    # ...
    
    raise Exception("Not yet implemented")

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

        # TODO: Potential speedup algorithm
        # table-based reprojection, so only have to reproject 100*100 values
        # instead of every single pixel
        # https://caniban.files.wordpress.com/2011/04/tile-based-geospatial-information-systems.pdf

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

def rasterize(vectordata, **rasterdef):

##    if "bbox" not in rasterdef:
##        # TODO: HANDLE FLIPPED COORDSYS AND/OR INTERPRETING VECTORDATA COORDSYS DIRECTION
##        # ...difficult since vector coord bbox is always min,max order,
##        # ...since no way to determine directions
##        rasterdef["bbox"] = vectordata.bbox

    # TODO: Add option to assign pixel value based on a feature valuefield
    # instead of just 0 and 1
    # ...

    raster = data.RasterData(mode="1bit", **rasterdef)

    # create 1bit image with specified size
    img = PIL.Image.new("1", (raster.width, raster.height), 0)
    drawer = PIL.ImageDraw.Draw(img)

    # set the coordspace to vectordata bbox
    a,b,c,d,e,f = raster.inv_affine

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
    raster.add_band(img=img)
    return raster

def vectorize(raster, bandnum=1):
    # so far only experimental
    # ...
    
    if raster.mode == "1bit":

        raise Exception("Not yet implemented")

        ##        import PIL.ImageMorph
        ##        op = PIL.ImageMorph.MorphOp(op_name="edge")
        ##        img = raster.bands[bandnum]
        ##        # extend img with 1 pixel border to allow identifying edges along the edge
        ##        # ...
        ##        # alt1
        ##        pixcount,outlineimg = op.apply(img)
        ##        # alt2
        ##        coords = op.match(img)
        ##
        ##        # difficult part is how to connect the edge pixels
        ##
        ##        # MAYBE:
        ##        # first get pixels as coordinates via geotransform
        ##        # start on first matching pixel
        ##        # then examine and follow first match among neighbouring pixels in clockwise direction
        ##        # each pixel followed is converted to coordinate via geotransform and added to a list
        ##        # keep following until ring is closed or no more neighbours have match (deadend)
        ##        # jump to next unprocessed pixel, and repeat until all have been processed
        ##        # after all is done, we have one or more polygons, lines in the case of deadends, or points in the case of just one match per iteration
        ##        # if polygons, identify if any of them are holes belonging to other polygons
        ##
        ##        # ALSO
        ##        # how to connect the pixels, via centerpoint coordinate, or tracing the cell corners?
        ##        # ...
        ##
        ##        # OR
        ##        # http://cardhouse.com/computer/vector.htm

    else:
        # for each region of contiguous cells with same value
        # assign a feature and give it that value
        # ...
        raise Exception("Not yet implemented")

def crop(raster, bbox):
    """Finds the pixels that are closest to the bbox
    and just does a normal image crop, meaning no resampling/changing of data.
    """
    x1,y1,x2,y2 = bbox

    # get nearest pixels of bbox coords
    px1,py1 = raster.geo_to_cell(x1,y1)
    px2,py2 = raster.geo_to_cell(x2,y2)

    # get new dimensions
    outrast = data.RasterData(**raster.meta)
    width = abs(px2-px1)
    height = abs(py2-py1)
    outrast.width = width
    outrast.height = height

    # crop each and add as band
    pxmin = min(px1,px2)
    pymin = min(py1,py2)
    pxmax = max(px1,px2)
    pymax = max(py1,py2)
    for band in raster.bands:
        img = band.img.crop((pxmin,pymin,pxmax,pymax))
        outrast.add_band(img=img, nodataval=band.nodataval)

    # update output geotransform based on crop corners
    x1,y1 = raster.cell_to_geo(px1,py1) 
    x2,y2 = raster.cell_to_geo(px2,py2)
    outrast.set_geotransform(width=width, height=height,
                             bbox=[x1,y1,x2,y2])
    return outrast

def clip(raster, clipdata, bbox=None):
    # TODO: ALSO HANDLE CLIP BY RASTER DATA

    from ..vector import VectorData
    from ..raster import RasterData
    
    if isinstance(clipdata, VectorData):

        # determine georef of out raster, defaults to that of the main raster
        if bbox:
            raster = crop(raster, bbox)
        
        # rasterize vector data
        georef = {"width":raster.width, "height":raster.height,
                  "affine":raster.affine}
        valid = rasterize(clipdata, **georef)

        # paste main raster onto blank image using rasterized as mask
        outrast = data.RasterData(mode=raster.mode, **georef)

        # clip and add each band
        for band in raster.bands:
            
            # paste data onto blank image where mask is true
            img = PIL.Image.new(band.img.mode, band.img.size, band.nodataval)
            img.paste(band.img, mask=valid.bands[0].img)
            outrast.add_band(img=img, nodataval=band.nodataval)

        return outrast

    elif isinstance(clipdata, RasterData):
        # create blank image
        # paste raster onto blank image using clip raster as mask
        pass
