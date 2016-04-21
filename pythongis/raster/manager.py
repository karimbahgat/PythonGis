
from . import data
##from .. import raster
##from .. import vector
from ..vector import sql

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

def warp(raster, tiepoints):
    # aka georeference
    # morph or smudge a raster in arbitrary directions based on a set of controlpoints
    # default algorithm is splines, maybe also polynomyal
    # prob first prep the tiepoints then call on analyzer.interpolate with splines method
    # ...
    
    raise Exception("Not yet implemented")

def reproject(raster, crs, algorithm="nearest", **rasterdef):

    raise Exception("Not yet implemented")
    
    ##    algocode = {"nearest":PIL.Image.NEAREST,
    ##                "bilinear":PIL.Image.BILINEAR,
    ##                "bicubic":PIL.Image.BICUBIC,
    ##                }[algorithm.lower()]
    ##
    ##    if crs == raster.crs:   # need pycrs to compare crs in a smarter way
    ##        raise Exception("The from and to crs are the same, so no need to reproject.")

    ##    # first, create target raster based on rasterdef
    ##    targetrast = data.RasterData(**rasterdef)
    ##    for band in raster:
    ##        targetrast.add_band(img=band.img)
    ##
    ##    # get target coordinates
    ##    lons = PIL.ImagePath.Path([targetrast.cell_to_geo(px,0) for px in range(targetrast.width)])
    ##    lats = PIL.ImagePath.Path([targetrast.cell_to_geo(0,py) for py in range(targetrast.height)])
    ##
    ##    # reproject coords using pyproj
    ##    for row,lat in enumerate(lats):
    ##        # convert crs coords
    ##        reproj = PIL.ImagePath.Path([pyproj.convert(lon,lat) for lon in lons])
    ##
    ##        # go from reprojected target coordinates and over to source pixels
    ##        sourcepixels = reproj.transform(raster.inv_affine)
    ##
    ##        # manually get and set the pixels using some algorithm
    ##        if algorithm == "nearest":
    ##            for sourceband,targetband in zip(raster,targetrast):
    ##                for col,pixel in enumerate(sourcepixels):
    ##                    pixel = int(round(pixel[0])),int(round(pixel[1]))
    ##                    val = sourceband.get(*pixel)
    ##                    targetband.set(col,row,val)

    # TODO: Potential speedup algorithm
    # table-based reprojection, so only have to reproject 100*100 values
    # instead of every single pixel
    # https://caniban.files.wordpress.com/2011/04/tile-based-geospatial-information-systems.pdf

def resample(raster, algorithm="nearest", **rasterdef):

    algocodes = {"nearest":PIL.Image.NEAREST,
                "bilinear":PIL.Image.BILINEAR,
                "bicubic":PIL.Image.BICUBIC,
                }
    
    # first, create target raster based on rasterdef
    targetrast = data.RasterData(mode=raster.mode, **rasterdef)

    # fast PIL transform methods
    if algorithm in algocodes:
        algocode = algocodes[algorithm.lower()] # resampling code used by PIL
        
        # get coords of all 4 target corners
        xleft,ytop = targetrast.cell_to_geo(0,0)
        xright,ybottom = targetrast.cell_to_geo(targetrast.width-1, targetrast.height-1)
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
            # if mask
            if band.nodataval != None:
                datatrans.paste(band.nodataval, mask=masktrans)
                
            # store image
            targetrast.add_band(img=datatrans, nodataval=band.nodataval)

    else:
        raise Exception("Not yet implemented")

    return targetrast

def align(raster, **rasterdef):
    rasterdef = rasterdef.copy()
    ref = data.RasterData(mode="1bit", **rasterdef)
    
    xscale,xskew,xoffset,yskew,yscale,yoffset = raster.meta["affine"]
    xoffset,yoffset = ref.meta["affine"][2], ref.meta["affine"][5]
    resampledef = {"width":raster.width,
                   "height":raster.height,
                   "affine":[xscale,xskew,xoffset,yskew,yscale,yoffset]}
    
    aligned = resample(raster, **resampledef)
    return aligned

def upscale(raster, stat="sum", **rasterdef):
    # either use focal stats followed by nearest resampling to match target raster
    # or use zonal stats where zone values are determined by col/row to form squares
    # for various approaches, see: https://gis.stackexchange.com/questions/27838/resample-binary-raster-to-give-proportion-within-new-cell-window/27849#27849

    # validate that in fact upscaling
    # ...
    
    # first resample to coincide with rasterdef
    targetrast = data.RasterData(mode="float32", **rasterdef)
    xscale,_,_, _,yscale,_ = targetrast.affine
    targetrast.bands = []
    for _ in raster:
        targetrast.add_band()

    # maybe align the valueraster to rasterdef by rounding the xoff and yoff to georef
    raster = align(raster, **rasterdef)

    # run moving focal window to group cells
    tilesize = (abs(xscale),abs(yscale))
    print tilesize
    for tile in tiled(raster, tilesize=tilesize, worldcoords=True):
        tilecenter = (tile.bbox[0]+tile.bbox[2])/2.0, (tile.bbox[1]+tile.bbox[3])/2.0
        targetpx = targetrast.geo_to_cell(*tilecenter)

        # for each tile band
        for bandnum,tileband in enumerate(tile.bands):
            
            # aggregate tile stats
            aggval = tileband.summarystats(stat)[stat]
            
            # set corresponding targetrast band cell value
            cell = targetrast.bands[bandnum].get(*targetpx)
            try:
                cell.value = aggval
            except IndexError:
                # HMMMMM.....
                ###print "Warning: upscale tile somehow spilling out of range..."
                ###tile.view(500,500)
                pass

    # visual inspection
##    from .. import renderer as r
##    m = r.MapCanvas(1000,1000)
##    m.zoom_bbox(*targetrast.bbox)
##    m.zoom_factor(-1.3)
##    m.layers.add_layer(r.RasterLayer(targetrast))
##    m.render_all()
##    for tile in tiled(raster, tilesize=tilesize, worldcoords=True):
##        tilecenter = (tile.bbox[0]+tile.bbox[2])/2.0, (tile.bbox[1]+tile.bbox[3])/2.0
##        m.drawer.draw_circle(tilecenter, fillsize="3px", fillcolor=None)
##    m.view()

    return targetrast
    

def downscale(raster, stat="spread", **rasterdef):
    # first, create target raster based on rasterdef
    targetrast = data.RasterData(mode=raster.mode, **rasterdef)
    
# Accurate vector geometric approach (WARNING: extremely slow)
##def accuresample(raster, algorithm="sum", **rasterdef):
##    # first, create target raster based on rasterdef
##    targetrast = data.RasterData(mode=raster.mode, **rasterdef)
##    
##    def point_in_poly(x,y,poly):
##        # taken from http://stackoverflow.com/questions/16625507/python-checking-if-point-is-inside-a-polygon
##        n = len(poly)
##        inside = False
##        p1x,p1y = poly[0]
##        for i in range(n+1):
##            p2x,p2y = poly[i % n]
##            if y > min(p1y,p2y):
##                if y <= max(p1y,p2y):
##                    if x <= max(p1x,p2x):
##                        if p1y != p2y:
##                            xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
##                        if p1x == p2x or x <= xints:
##                            inside = not inside
##            p1x,p1y = p2x,p2y
##        return inside
##
##    # ensure correct outdatatype
##    if (raster.mode.startswith("float") and algorithm != "count") or (algorithm in "average stddev".split()):
##        targetrast.convert("float32")
##
##    # add empty bands
##    for band in raster:
##        targetrast.add_band()
##
##    # aggregate overlapping
##    def find_overlapping_cells(cell, band):
##        cellcorners = cell.poly["coordinates"][0]
##        for othercell in band:
##            if point_in_poly(othercell.x, othercell.y, cellcorners):
##                yield othercell
##
##    for band in targetrast.bands:
##        prevrow = None
##        for cell in band:
##            if cell.value != band.nodataval:
##                if cell.row != prevrow:
##                    print prevrow
##                    prevrow = cell.row
##                croppedvals = crop(raster, cell.bbox) # same as a quick spatial index of possibly relevant cells
##                for valband in croppedvals.bands:
##                    overlapping = find_overlapping_cells(cell, valband) # TODO: optimize so dont have to repeat for each band
##                    aggval = sql.aggreg(overlapping, [("aggval",lambda c: c.value, algorithm)])[0]
##                    ###print aggval
##                    cell.value = aggval

def rasterize(vectordata, valuekey=None, **rasterdef):
    # TODO: When using valuekey, how to choose between/aggregate
    # overlapping or nearby features? Now just overwrites and uses value of
    # the last feature. Maybe provide aggfunc option?
    # See further below.

    if valuekey:
        raise Exception("Rasterizing with valuekey not yet implemented")

    mode = "float32" if valuekey else "1bit"
    raster = data.RasterData(mode=mode, **rasterdef)

    # create 1bit image with specified size
    mode = "F" if valuekey else "1"
    img = PIL.Image.new(mode, (raster.width, raster.height), 0)
    drawer = PIL.ImageDraw.Draw(img)

    # set the coordspace to vectordata bbox
    a,b,c,d,e,f = raster.inv_affine

    # draw the vector data
    for feat in vectordata:
        val = float(valuekey(feat)) if valuekey else 1.0
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
                drawer.polygon(path, fill=val, outline=None)
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
                drawer.line(path, fill=val)
            
        # point, 1 pixel square size
        elif "Point" in geotype:
            path = PIL.ImagePath.Path(coords)
            path.transform((a,b,c,d,e,f))
            drawer.point(path, fill=val)

    # if valuekey mode,
    #    find self intersections,
    #    aggregate their values,
    #    and draw over those parts with the new aggval
    # OR maybe not,
    #    instead must test multiple overlap per cell?
    # ...

    # create raster from the drawn image
    raster.add_band(img=img)
    return raster

def vectorize(raster, mergecells=False, metavars=False, bandnum=0):
    # so far only experimental
    # ...

    from ..vector.data import VectorData

    if mergecells:
        
        # merge/union cells of same values
        
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

    else:
        
        # separate feature and geometry for each cell
        
        outvec = VectorData()

        if metavars:
            outvec.fields = ["col","row","x","y","val"]
            band = raster.bands[bandnum]
            nodataval = band.nodataval
            for cell in band:
                if cell.value != nodataval:
                    row = [cell.col, cell.row, cell.x, cell.y, cell.value]
                    outvec.add_feature(row=row, geometry=cell.poly)
        else:
            outvec.fields = ["val"]
            band = raster.bands[bandnum]
            nodataval = band.nodataval
            for cell in band:
                if cell.value != nodataval:
                    row = [cell.value]
                    outvec.add_feature(row=row, geometry=cell.poly)

        return outvec

def crop(raster, bbox, worldcoords=True):
    """Finds the pixels that are closest to the coordinate bbox
    and just does a normal image crop, meaning no resampling/changing of data.
    """
    x1,y1,x2,y2 = bbox
    xscale,xskew,xoffset, yskew,yscale,yoffset = raster.meta["affine"]

    if worldcoords:
        # bbox is only used manually by user and should include the corners (+- half cellsize)
        # need to remove this padding to get it right
        if x2 > x1:
            x1 += xscale/2.0
            x2 -= xscale/2.0
        else:
            x1 -= xscale/2.0
            x2 += xscale/2.0
        if y2 > y1:
            y1 += yscale/2.0
            y2 -= yscale/2.0
        else:
            y1 -= yscale/2.0
            y2 += yscale/2.0

        # get nearest pixels of bbox coords
        px1,py1 = raster.geo_to_cell(x1,y1)
        px2,py2 = raster.geo_to_cell(x2,y2)
    else:
        # already in pixels
        px1,py1,px2,py2 = x1,y1,x2,y2

    # PIL doesnt include the max pixel coords
    px2 += 1
    py2 += 1

    # get new dimensions
    outrast = data.RasterData(**raster.meta)
    width = abs(px2-px1)
    height = abs(py2-py1)
    if width == 0 or height == 0:
        raise Exception("Cropping bbox was too small, resulting in 0 pixels")
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

    # update output affine offset based on new upperleft corner
    x1,y1 = raster.cell_to_geo(px1,py1)
    outrast.set_geotransform(xoffset=x1, yoffset=y1)

    return outrast

def tiled(raster, tilesize=None, tiles=(10,10), worldcoords=False):
    """Yields raster as a series of subtile rasters"""
    if tilesize:
        tw,th = tilesize

    elif tiles:
        tw,th = raster.width // tiles[0], raster.height // tiles[1]
        worldcoords = False

    else:
        raise Exception("Either tiles or tilesize must be specified")

    if worldcoords:
        xscale,xskew,xoffset, yskew,yscale,yoffset = raster.meta["affine"]
        x1,y1 = raster.cell_to_geo(0,0)
        x2,y2 = raster.cell_to_geo(raster.width-1,raster.height-1)
            
        xfrac,yfrac = tw / abs(x2-x1), th / abs(y2-y1) 
        tw,th = int(round(raster.width*xfrac)), int(round(raster.height*yfrac))

    minw,minh = 0,0
    maxw,maxh = raster.width,raster.height

    def _floatrange(fromval,toval,step):
        # handles both ints and flots
        val = fromval
        while val <= toval:
            yield val
            val += step
    
    for row in _floatrange(minh, maxh, th):
        row2 = row+th if row+th <= maxh else maxh
        for col in _floatrange(minw, maxw, tw):
            col2 = col+tw if col+tw <= maxw else maxw
            try:
                tile = crop(raster, [col,row,col2,row2], False)
                yield tile
            except:
                # HMMM, tile was too small...
                pass

def clip(raster, clipdata, bbox=None, bandnum=0):
    """Clips a raster by the areas containing data in a vector or raster data instance.
    If clipdata is a raster instance, the valid area is determined from the specified
    bandnum arg (default is 0). 
    """

    from ..vector.data import VectorData
    from ..raster.data import RasterData


    # limit to bbox area
    if bbox:
        raster = crop(raster, bbox)

    # determine georef of out raster, defaults to that of the main raster
    georef = {"width":raster.width, "height":raster.height,
              "affine":raster.affine}
    outrast = data.RasterData(mode=raster.mode, **georef)

    # get band of valid areas
    if isinstance(clipdata, VectorData):
        # rasterize vector data
        valid = rasterize(clipdata, **georef).bands[0]
    elif isinstance(clipdata, RasterData):
        # get boolean band where nodatavals
        valid = clipdata.bands[bandnum].conditional("val != %s" % clipdata.bands[bandnum].nodataval)

    # clip and add each band
    for band in raster.bands:
        
        # paste data onto blank image where 'valid' is true
        img = PIL.Image.new(band.img.mode, band.img.size, band.nodataval)
        img.paste(band.img, mask=valid.img)
        outrast.add_band(img=img, nodataval=band.nodataval)

    return outrast

