"""
Module containing methods for the management and modification of raster datasets. 
"""

from . import data
from ..vector import sql

import PIL, PIL.Image, PIL.ImageDraw, PIL.ImagePath, PIL.ImageChops, PIL.ImageMath
import gc

def mosaic(rasters, overlaprule="last", **rasterdef):
    """
    Mosaic rasters covering different areas together into one file.
    All rasters are aligned to the extent and resolution of the first
    raster, though this can be overridden by the optional rasterdef.
    Parts of the rasters may overlap each other, in which case we use the
    overlap rule. Valid overlap rules: last (default), first.

    TODO: Add more overlap rules. 
    """
    # use resampling to the same dimensions as the first raster
    rasterdef = rasterdef or rasters[0].rasterdef
    # TODO: Also set total bbox and dims to combined bboxes...
    outrast = data.RasterData(mode=rasters[0].mode, **rasterdef)
    maxbands = max((len(rast) for rast in rasters))
    # align to common grid
    rasters = [align(rast, **rasterdef) for rast in rasters]
    # paste
    for i in range(maxbands):
        outband = outrast.add_band()
        if overlaprule == "last":
            for rast in rasters:
                if len(rast) >= i:
                    outband.img.paste(rast.bands[i].img, (0,0), rast.mask)
        elif overlaprule == "first":
            for rast in reversed(rasters):
                if len(rast) >= i:
                    outband.img.paste(rast.bands[i].img, (0,0), rast.mask)
        elif overlaprule == "sum":
            # if image bbox overlap
            # find overlap via img1 & img2
            # use img1 + img2 via math
            # paste using overlap as mask
            raise NotImplemented("Overlap rule not supported")
        else:
            raise NotImplemented("Overlap rule not supported")

    return outrast

def warp(raster, tiepoints):
    """
    NOT YET IMPLEMENTED

    Morph or smudge a raster in arbitrary directions based on a set of controlpoints.
    Default algorithm is splines, maybe also polynomyal.

    Aka: georeference.
    """
    # Prob first prep the tiepoints then call on analyzer.interpolate with splines method
    
    raise NotImplementedError

def reproject(raster, crs, algorithm="nearest", **rasterdef):
    """
    NOT YET IMPLEMENTED

    Reprojects the raster from the input crs to a target crs.
    If given, **rasterdef will override the input raster structure.
    """
    
    raise NotImplementedError

    # TODO: How to handle coords that get transformed to infinity...

    import pyproj
    
    algocode = {"nearest":PIL.Image.NEAREST,
                "bilinear":PIL.Image.BILINEAR,
                "bicubic":PIL.Image.BICUBIC,
                }[algorithm.lower()]

    if crs == raster.crs:   # need pycrs to compare crs in a smarter way
        raise Exception("The from and to crs are the same, so no need to reproject.")

    fromcrs = pyproj.Proj(raster.crs)
    tocrs = pyproj.Proj(crs)

    # first, create target raster based on rasterdef
    rasterdef = rasterdef or raster.rasterdef
    targetrast = data.RasterData(mode=raster.mode, **rasterdef)
    for band in raster:
        targetrast.add_band(img=band.img)

    # get target coordinates
    lons = PIL.ImagePath.Path([targetrast.cell_to_geo(px,0) for px in range(targetrast.width)])
    lats = PIL.ImagePath.Path([targetrast.cell_to_geo(0,py) for py in range(targetrast.height)])

    # reproject coords using pyproj
    for row,lat in enumerate(lats):
        # convert crs coords
        reproj = PIL.ImagePath.Path([pyproj.transform(fromcrs,tocrs,lon,lat) for lon in lons])

        # go from reprojected target coordinates and over to source pixels
        sourcepixels = reproj.transform(raster.inv_affine)

        # manually get and set the pixels using some algorithm
        if algorithm == "nearest":
            for sourceband,targetband in zip(raster,targetrast):
                for col,pixel in enumerate(sourcepixels):
                    pixel = int(round(pixel[0])),int(round(pixel[1]))
                    val = sourceband.get(*pixel)
                    targetband.set(col,row,val)
        else:
            raise NotImplementedError("Not a valid algorithm")

##    # first, create target raster based on rasterdef
##    rasterdef = rasterdef or raster.rasterdef
##    # TODO: need to calc xscale yscale based on reprojected bbox?
##    # ... 
##    targetrast = data.RasterData(mode=raster.mode, **rasterdef)
##    for band in raster:
##        targetrast.add_band(img=band.img)
##
##    # get target coordinates
##    coords = [targetrast.cell_to_geo(px,py) for px in range(targetrast.width) for py in range(targetrast.height)]
##    lons,lats = zip(*coords)
##
##    # reproject coords using pyproj
##    nlons,nlats = pyproj.transform(fromcrs,tocrs,lons,lats)
##    xmin,xmax = min(nlons),max(nlons)
##    ymin,ymax = min(nlats),max(nlats)
##
##    # manually get and set the pixels using some algorithm
##    if algorithm == "nearest":
##        for row in range(targetrast.height):
##            for col in range(targetrast.width):
##                i = row * targetrast.height + col
##                nlon = nlons[i]
##                nlat = nlats[i]
##
##                # hmm...
##                
##                pixel = raster.geo_to_cell(nlon,nlat)
##                print pixel
##                for sourceband,targetband in zip(raster,targetrast):
##                    val = sourceband.get(*pixel).value
##                    print val
##                    targetband.set(col,row,val)
##    else:
##        raise NotImplementedError("Not a valid algorithm")

    return targetrast

    # TODO: Potential speedup algorithm
    # table-based reprojection, so only have to reproject 100*100 values
    # instead of every single pixel
    # https://caniban.files.wordpress.com/2011/04/tile-based-geospatial-information-systems.pdf

def resample(raster, algorithm="nearest", **rasterdef):
    """Resamples raster extent, resolution, or affine transform.
    Algorithm for resampling can be nearest (default), bilinear, bicubic."""

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

        # transform the mask too
        # note: if we don't invert the mask, the transform will form a nontransparent outer edge
        masktrans = PIL.ImageChops.invert(raster.mask.convert("L"))
        masktrans = masktrans.transform((targetrast.width,targetrast.height),
                                            PIL.Image.QUAD,
                                            flattened,
                                            resample=algocode)
        masktrans = PIL.ImageChops.invert(masktrans).convert("1") # invert back

        # transform each band
        for band in raster.bands:
            datatrans = band.img.transform((targetrast.width,targetrast.height),
                                            PIL.Image.QUAD,
                                            flattened,
                                            resample=algocode)
            # set mask cells to nullvalue
            if band.nodataval != None:
                datatrans.paste(band.nodataval, mask=masktrans)
                
            # add band
            targetrast.add_band(img=datatrans, nodataval=band.nodataval)

        targetrast.mask = masktrans

    else:
        raise Exception("Not yet implemented")

    return targetrast

def roll(raster, x, y, worldcoords=True):
    """Offsets the cell values along the x and/or y axis, wrapping any
    overflowing cells around to the opposite edge.
    Useful for recentering the midpoint of a raster dataset.
    By default the offset values are given as units in the raster's
    coordinate system, but can also be given as pixel cells by setting
    worldcoords to False. 
    Does not affect the raster's affine geotransform. 

    Aka: wrap.
    """
    out = raster.copy()
    xscale, xskew, xoffset, yskew, yscale, yoffset = out.affine

    # roll the data
    if worldcoords:
        x = int(round( x / float(xscale) ))
        y = int(round( y / float(yscale) ))
    premask = out.mask
    for band in out.bands:
        band.img = PIL.ImageChops.offset(band.img, x, y)
        band.mask = PIL.ImageChops.offset(band.mask, x, y)
    out.mask = PIL.ImageChops.offset(premask, x, y)
    
    return out

def align(raster, **rasterdef):
    """Aligns a raster to the given rasterdef (via resampling), so that
    the x/yoffset starts on the same x/yoffset as the rasterdef.
    """
    # TODO: Not sure if should use same x/yoffset or just as a multiple...
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
    """Upscales a raster so that many cells are aggregated to fewer cells.
    Works by running a moving window coinciding with each new cell in the
    new rasterdef resolution, setting the new cell to the summary statistics of
    the moving window.
    Stat decides which summary statistic to use when aggregating (defaults to sum). 
    """
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

    return targetrast
    

def downscale(raster, stat="spread", **rasterdef):
    """
    NOT YET IMPLEMENTED

    Downscales a raster so that few cells are spread across many new cells. 
    """
    # first, create target raster based on rasterdef
    targetrast = data.RasterData(mode=raster.mode, **rasterdef)

    raise NotImplementedError()


def rasterize(vectordata, valuekey=None, stat=None, priority=None, partial=None, **rasterdef):
    """
    Rasterizes vectordata to a raster with the given rasterdef. 
    By default returns an 8-bit raster with 1 for the location of vector features. 
    If valuekey func, the cells take on the value of each feature and multiple
    feats in a cell are aggregated using stat.
    If priority func, multiple feats are filtered/chosen before aggregated. 
    If partialfunc, feats that only partially overlap cell are given a weight.

    TODO: For non-valuekey, it currently returns an 8bit L raster with 0/1,
        or should it return a binary raster with 0/255 (PIL weirdness)?
        Or maybe binary rasters should be changed so uses 0/1 somehow...?
    """

    # TODO: allow 'custom' which instead sets every cell using custom method taking cell and feats (slow but flexible)

    mode = "float32" if valuekey else "int8"
    raster = data.RasterData(mode=mode, **rasterdef)

    # create 1bit image with specified size
    mode = "F" if valuekey else "L"  # L aka 8bit instead of 1, temp fix because in mode 1, actually writes 255
    img = PIL.Image.new(mode, (raster.width, raster.height), 0)
    drawer = PIL.ImageDraw.Draw(img)

    # drawing procedure
    def burn(val, feat, drawer):
        geotype = feat.geometry["type"]

        # set the coordspace to vectordata bbox
        a,b,c,d,e,f = raster.inv_affine

        # if fill val is None, then draw binary outline
        fill = val
        outline = 1.0 if val is None else None
        holefill = 0.0 if val is not None else None
        holeoutline = 1.0 if val is None else None
        #print ["burnmain",fill,outline,"burnhole",holefill,holeoutline]

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
                drawer.polygon(path, fill=fill, outline=outline)
                # holes
                if len(poly) > 1:
                    for hole in poly[1:]:
                        hole = [tuple(p) for p in hole]
                        path = PIL.ImagePath.Path(hole)
                        path.transform((a,b,c,d,e,f))
                        drawer.polygon(path, fill=holefill, outline=holeoutline)
                        
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

    # quickly draw all vector data
    for feat in vectordata:
        if not feat.geometry:
            continue
        val = float(valuekey(feat)) if valuekey else 1.0
        burn(val, feat, drawer)

    # create raster from the drawn image
    outband = raster.add_band(img=img, nodataval=None)

    # special pixels
    if valuekey:
        if not stat:
            raise Exception("Valuekey and stat must be set at the same time")
            
        multimask = PIL.Image.new("1", (raster.width,raster.height))
        multidrawer = PIL.ImageDraw.Draw(multimask)

        if not hasattr(vectordata, "spindex"):
            vectordata.create_spatial_index()

        # prepare geometries
        from shapely.prepared import prep
        for f in vectordata:
            f._shapely = f.get_shapely()
            f._prepped = prep(f._shapely)

        # burn all self intersections onto mask (constant time, slower for easy small geoms)
        for f1 in vectordata:
            if not f1.geometry:
                continue
            print ["f1",f1.id,len(vectordata)]

            # first burn all maybe feats (ie get their combined union)
            img2 = PIL.Image.new("1", (raster.width,raster.height))
            d2 = PIL.ImageDraw.Draw(img2)
            for f2 in vectordata.quick_overlap(f1.bbox):
                if not f2.geometry:
                    continue
                if f1 is not f2:
                    burn(1.0, f2, d2)

            # if any, then get common raster intersection with main feat
            if img2.getbbox():
                img1 = PIL.Image.new("1", (raster.width,raster.height))
                d1 = PIL.ImageDraw.Draw(img1)
                burn(1.0, f1, d1)
                intsec = PIL.ImageMath.eval("convert(img1 & img2, '1')", img1=img1, img2=img2)
                multimask.paste(1, mask=intsec)

        # burn the outlines of polygons (border cells may not be overlapping but can still contain multiple choices)
        partialmask = PIL.Image.new("1", (raster.width,raster.height))
        partialdrawer = PIL.ImageDraw.Draw(partialmask)
        for feat in vectordata:
            if not feat.geometry:
                continue
            burn(None, feat, partialdrawer)

        # aggregate feats for each burned cell in mask
        from ..vector import sql
        from shapely.geometry import asShape
        from shapely.prepared import prep
        from time import time
        
        # get which cells to calculate
        multipix = multimask.load()
        partialpix = partialmask.load()

        for y in range(raster.height):
            print "%r of %r"%(y,raster.height)
            for x in range(raster.width):
                multicell = multipix[x,y]
                partialcell = partialpix[x,y]

                # single values have already been written, now only overwrite multis or partials
                if multicell or partialcell:
                    cell = outband.get(x, y)
                    cellgeom = asShape(cell.poly)
                    
                    # get features in that cell
                    spindex = list(vectordata.quick_overlap(cellgeom.bounds))
                    intsecs = [feat for feat in spindex
                               if feat.geometry and not feat._prepped.disjoint(cellgeom)]
                    if not intsecs:
                        continue

                    # filter or choose multiple feats in a cell
                    if priority and (multicell or partialcell) and len(intsecs) > 1:
                        intsecs = priority(cellgeom, intsecs)

                    # get feature values
                    vals = [valuekey(feat) for feat in intsecs]

                    # calculate and apply weight for cells where features are only partially present
                    if partial and partialcell:
                        vals = [v * partial(cellgeom, feat) for v,feat in zip(vals,intsecs)]

                    # aggregate stat if multiple
                    if len(vals) > 1:
                        value = sql.aggreg(vals, [("val", lambda v: v, stat)])[0]
                    else:
                        value = vals[0]

                    # finally set
                    #print ["set","%r of %r"%(y,raster.height),(x,y),len(intsecs),value]
                    outband.set(x, y, value)

    return raster

def vectorize(raster, mergecells=True, metavars=True, bandnum=0):
    """
    Vectorizes a raster band (defaults to 0) to vector data. 
    By default merges cells of same value into polygons.
    Non-binary rasters will create separate polygons for each
    contiguous group of cells with same value. 
    
    Setting mergecells to False will create separate polygon for each cell.
    Metavars will add extra fields about the position of each cell.
    """

    from ..vector.data import VectorData

    if mergecells:
        
        # merge/union cells of same values

        import shapely
        from shapely.geometry import Polygon, LineString, Point
        
        if raster.mode == "1bit":

##            import PIL.ImageMorph
##            op = PIL.ImageMorph.MorphOp(op_name="edge")
##            img = raster.bands[bandnum].img
##            # extend img with 1 pixel border to allow identifying edges along the edge
##            # ...
##            
##            pixcount,outlineimg = op.apply(img)
##            outlinepix = outlineimg.load()
##            outlineimg.show()
##            
##            active = op.match(img)

            # difficult part is how to connect the edge pixels

            # Approach 1: Center-point
            # first get pixels as coordinates via geotransform
            # start on first matching pixel
            # then examine and follow first match among neighbouring pixels in clockwise direction
            # each pixel followed is converted to coordinate via geotransform and added to a list
            # keep following until ring is closed or no more neighbours have match (deadend)
            # jump to next unprocessed pixel, and repeat until all have been processed
            # after all is done, we have one or more polygons, lines in the case of deadends, or points in the case of just one match per iteration
            # if polygons, identify if any of them are holes belonging to other polygons

##            outvec = VectorData()
##
##            def right(dirr):
##                xoff,yoff = dirr
##                # ...
##
##            def neighbour(prev,cur):
##                x,y = cur
##                if not prev:
##                    prev = x,y-1 # pretend came from top so will go down
##                dirr = x-prev[0],y-prev[1]
##                for _ in range(8):
##                    xoff,yoff = right(dirr)
##                    nx,ny = x+xoff,y+yoff
##                    # neighbouring on-pixel, but cannot go back
##                    if (nx,ny) not in (prev,cur) and outlinepix[nx,ny]:
##                        yield nx,ny
##                    dirr = right((xoff,yoff))
##
##            parts = []
##            while active:
##                print len(active)
##                path = []
##                
##                # can only start new feat on an active non-visited cell, but can follow any on-pixel
##                prev = None
##                cur = active[0]
##                while cur:
##                    #print cur
##                    path.append(cur)
##                    if cur in active:
##                        active.remove(cur)
##                    
##                    connections = list(neighbour(prev, cur))
##                    if not connections:
##                        # reached deadend, ie nowhere else to go
##                        break
##                    nxt = connections[0]
##                    if nxt == path[0]:
##                        # circled back to start
##                        path.append(nxt)
##                        break
##                    elif nxt in path:
##                        # hit back on itself, ie infinite loop, ie selfintersection
##                        path.append(nxt)
##                        break
##                    elif len(connections) > 2:
##                        # reached a junction, ie more than two possible next direction
##                        path.append(nxt)
##                        break
##                    prev = cur
##                    cur = nxt
##
##                # finished, add part
##                # polygon, ie path has been closed
##                #print len(path)
##                if len(path) > 1:# and path[0]==path[-1]:
##                    parts.append(LineString(path))
##                else:
##                    pass #parts.append(Point(path[0]))
##
##            # connect line segments into polygons
##            print len(parts)
##            for poly in shapely.ops.polygonize(parts):
##                print str(poly)[:100]
##                outvec.add_feature([], poly.__geo_interface__)
##
##            return outvec

            # Approach 2: cell outline
            # http://cardhouse.com/computer/vector.htm

            # Approach 3: shapely cell merge
            band = raster.bands[bandnum]
            shps = []
            for i,cell in enumerate(band):
                if cell.value:
                    #print i
                    shp = Polygon(cell.poly["coordinates"][0])
                    shps.append(shp)
            union = shapely.ops.cascaded_union(shps)
            print str(union)[:200]

            outvec = VectorData()
            outvec.fields = ["id"]
            for i,poly in enumerate(union.geoms):
                outvec.add_feature([i], poly.__geo_interface__)

            return outvec

        else:
            # for each region of contiguous cells with same value
            # assign a feature and give it that value
            outvec = VectorData()
            outvec.fields = ["value"]
            
            band = raster.bands[bandnum]
            zonevalues = (val for count,val in band.img.getcolors(raster.width*raster.height))
            for zoneval in zonevalues:
                print zoneval
                
                # exclude nullzone
                if zoneval == band.nodataval: continue

                shps = []
                for cell in band:
                    if cell.value == zoneval:
                        shp = Polygon(cell.poly["coordinates"][0])
                        shps.append(shp)

                union = shapely.ops.cascaded_union(shps)
                print str(union)[:200]

                if hasattr(union, "geoms"):
                    for poly in union.geoms:
                        outvec.add_feature([zoneval], poly.__geo_interface__)
                else:
                    outvec.add_feature([zoneval], union.__geo_interface__)

            return outvec


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
    The cropping bbox can also be set in pixel units if setting worldcoords to False. 
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

    # do bounds check
    pxmin = min(px1,px2)
    pymin = min(py1,py2)
    pxmax = max(px1,px2) 
    pymax = max(py1,py2)
    
    pxmin = max(0, pxmin)
    pymin = max(0, pymin)
    pxmax = min(raster.width-1, pxmax)
    pymax = min(raster.height-1, pymax)

    #print pxmin,pymin,pxmax,pymax

    if pxmax < 0 or pxmin > raster.width or pymax < 0 or pymin > raster.height:
        raise Exception("The cropping bbox is entirely outside the raster extent")

    # get new dimensions
    outrast = data.RasterData(**raster.meta)
    width = abs(pxmax-pxmin)
    height = abs(pymax-pymin)
    if width <= 0 or height <= 0:
        raise Exception("Cropping bbox was too small, resulting in 0 pixels")
    outrast.width = width
    outrast.height = height

    print width,height

    # crop each and add as band
    for band in raster.bands:
        img = band.img
        if hasattr(img, 'filename') and hasattr(img, 'tile') and len(img.tile) > 1:
            # not yet loaded, so open as new img and only load relevant tiles
            fn = img.filename
            encoding,firstbox,firstoffset,extra = img.tile[0]
            #print img.tile[0]
            if encoding == 'raw':
                # raw encoding, so should be able to custom specify our own tile
                # TODO: Not working properly for now so defaulting to compressed approach below
                
                # TODO: Do we also need to offset+subindex into specific bandnum if rgb etc?

                # ALT1, using tile option
                #dbyte = {'float32':4,'float16':2,'int32':4,'int16':2,'int8':1,'1bit':1}[band.mode]
                #print pxmin,pymin,pxmax,pymax
                #offset = ( (pymin*band.width) + pxmin) * dbyte
                #print dbyte,offset
                #img = PIL.Image.open(fn)
                #img.tile = [(encoding, (0,0,width,height), firstoffset + offset, extra)]
                #img.size = width,height
                #img.load() # = img.crop((pxmin,pymin,pxmax,pymax))

##                # ALT2, raw byte reading
##                import struct
##                with open(fn, 'rb') as fobj:
##                    # TODO: support more formats?? 
##                    dbyte = {'float32':4,'float16':2,'int32':4,'int16':2,'int8':1,'1bit':1}[band.mode]
##                    dtype = {'float32':'f','int32':'i','int16':'h','int8':'b','1bit':'b'}[band.mode]
##                    skipleft = pxmin * dbyte
##                    skipright = (band.width - (pxmin + width)) * dbyte
##                    #print pxmin,pymin,pxmax,pymax
##                    lineformat = '{l}x{w}{typ}{r}x'.format(l=skipleft, r=skipright, w=width, typ=dtype)
##                    #print lineformat
##                    frmt = lineformat * height
##                    
##                    offset = pymin * band.width * dbyte
##                    fobj.seek(firstoffset + offset)
##                    sz = struct.calcsize(frmt)
##                    #print 'sz',sz
##                    raw = fobj.read(sz)
##                    vals = struct.Struct(frmt).unpack(raw)
##                    #print len(vals)#, str(vals)[:100]
##
##                    # create the image from data
##                    #img = PIL.Image.frombytes(img.mode, (width,height), vals)
##                    img = PIL.Image.new(img.mode, (width,height), 0)
##                    #img.putdata(vals) # ideal, but slowly leaks memory, see https://github.com/python-pillow/Pillow/issues/1187
##                    pixels = img.load()
##                    for i,val in enumerate(vals):
##                        r = i // width
##                        c = i - (r*width)
##                        pixels[c,r] = val
##                    #import gc
##                    del lineformat,offset,sz,frmt,raw,vals
##                    gc.collect()

                # ALT3, linewise, directly into array, virtually no memory use and yet fast                
                import array
                img = PIL.Image.new(img.mode, (width,height), band.nodataval)
                pixels = img.load()
                with open(fn, 'rb') as fobj:
                    # TODO: support more formats?? 
                    dbyte = {'float32':4,'float16':2,'int32':4,'int16':2,'int8':1,'1bit':1}[band.mode]
                    arrtype = {'float32':'f','int32':'l','int16':'i','int8':'b','1bit':'b'}[band.mode]
                    skipleft = pxmin * dbyte
                    #print pxmin,pymin,pxmax,pymax

                    for r in range(height):
                        origrow = pymin + r
                        offset = ( (origrow*band.width) + pxmin) * dbyte
                        fobj.seek(firstoffset + offset)
                        linevals = array.array(arrtype)
                        linevals.fromfile(fobj, width)
                        for c,val in enumerate(linevals):
                            pixels[c,r] = val
                    
            else:
                # compressed, so must use existing tiles,
                # but can simply filter to those that overlap,
                # and img.crop will load only those tiles and batch crop them fast
                tiles = [(tenco,(txmin,tymin,txmax,tymax),offset,textra)
                         for tenco,(txmin,tymin,txmax,tymax),offset,textra in img.tile
                         if not (txmax < pxmin or txmin > pxmax or tymax < pymin or tymin > pymax)]
                #print 'len',len(tiles),len(img.tile)
                img = PIL.Image.open(fn)
                img.tile = tiles
                img = img.crop((pxmin,pymin,pxmax,pymax))

                # OLD: iterate and stitch together existing tiles, but so much IO is super slow
##                tiles = list(img.tile)
##                img = PIL.Image.new(img.mode, (width,height), 0)
##                for _,(txmin,tymin,txmax,tymax),offset,_ in tiles:
##                    if txmax < pxmin or txmin > pxmax or tymax < pymin or tymin > pymax:
##                        continue
##                    else:
##                        src = PIL.Image.open(fn)
##                        src.tile = [(encoding, (txmin,tymin,txmax,tymax), offset, extra)]
##                        #src.size = txmax-txmin, tymax-tymin
##                        src = src.crop((txmin,tymin,txmax,tymax))
##                        #print src, str(src.getcolors())[:100]
##                        
##                        # TODO: calc xypos to paste in new img
##                        nxmin = txmin-pxmin
##                        nymin = tymin-pymin
##                        #print (pxmin,pymin,pxmax,pymax),(txmin,tymin,txmax,tymax)
##                        #print nxmin,nymin,src.size
##                        
##                        img.paste(src, (nxmin,nymin))
                    
        else:
            img = img.crop((pxmin,pymin,pxmax,pymax))
        outrast.add_band(img=img, nodataval=band.nodataval)

    # update output affine offset based on new upperleft corner
    x1,y1 = raster.cell_to_geo(pxmin,pymin)
    outrast.set_geotransform(xoffset=x1, yoffset=y1)

    return outrast

def tiled(raster, tilesize=None, tiles=(10,10), worldcoords=False, bbox=None):
    """
    Iterates through raster as a series of subtile rasters.
    Tiles are determined either by tilesize or tiles args.
    Bbox is optional and will check so only yields tiles relevant to
    the given bbox. However, tiles will not be cropped, so may extend
    outside area of interest.

    By default tilesize and bbox are given as pixel cell units, but can be
    specified using coordinate system units by setting worldcoords to False. 
    """
    # TODO: not sure if tiles should be cropped to the bbox or just
    # used as selection criteria...
    
    if tilesize:
        tw,th = tilesize

    elif tiles:
        tw,th = raster.width // tiles[0], raster.height // tiles[1]
        worldcoords = False

    else:
        raise Exception("Either tiles or tilesize must be specified")

    if bbox:
        x1,y1,x2,y2 = bbox
        bcol1,brow1 = raster.geo_to_cell(x1,y1) 
        bcol2,brow2 = raster.geo_to_cell(x2,y2)
        if bcol2 < bcol1: bcol1,bcol2 = bcol2,bcol1
        if brow2 < brow1: brow1,brow2 = brow2,brow1

    if worldcoords:
        xscale,xskew,xoffset, yskew,yscale,yoffset = raster.meta["affine"]
        x1,y1 = raster.cell_to_geo(0,0)
        x2,y2 = raster.cell_to_geo(raster.width-1,raster.height-1)
            
        xfrac,yfrac = tw / abs(x2-x1), th / abs(y2-y1) 
        tw,th = int(round(raster.width*xfrac)), int(round(raster.height*yfrac))

    minw,minh = 0,0
    maxw,maxh = raster.width-1,raster.height-1

    def _floatrange(fromval,toval,step):
        # handles both ints and flots
        val = fromval
        while val <= toval:
            yield val
            val += step
    
    for row in _floatrange(minh, maxh-1, th):
        row2 = row+th-1 if row+th <= maxh else maxh-1

        if bbox and (brow2 <= row or brow1 >= row2):
            # dont yield if outside desired bbox
            continue
        
        for col in _floatrange(minw, maxw, tw):
            col2 = col+tw-1 if col+tw <= maxw else maxw-1

            if bbox and (bcol2 <= col or bcol1 >= col2):
                # dont yield if outside desired bbox
                continue

            tile = crop(raster, [col,row,col2,row2], False)
            yield tile

##            try:
##                tile = crop(raster, [col,row,col2,row2], False)
##                yield tile
##            except:
##                # HMMM, tile was too small...
##                pass

def clip(raster, clipdata, bbox=None, bandnum=0):
    """Clips a raster by the areas containing data in a vector or raster data instance.
    If clipdata is a vector instance, the vector is first rasterized. 
    If clipdata is a raster instance, the valid area is determined from the non-nodata cells
    of the specified bandnum arg (default is 0).
    The clipping can be further limited to the bbox arg. 
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
        valid = valid.conditional("val > 0") # necessary bc rasterize returns 8bit instead of binary
    elif isinstance(clipdata, RasterData):
        # get boolean band where nodatavals
        valid = clipdata.bands[bandnum].conditional("val != %s" % clipdata.bands[bandnum].nodataval)

    # clip and add each band
    for band in raster.bands:
        
        # paste data onto blank image where 'valid' is true
        img = PIL.Image.new(band.img.mode, band.img.size, 0) # avoid initializing with None, bc sometimes results in pixel noise
        if band.nodataval != None: img.paste(band.nodataval) # set background to nodataval
        img.paste(band.img, mask=valid.img)
        outrast.add_band(img=img, nodataval=band.nodataval)

    return outrast

