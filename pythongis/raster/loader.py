
# import internals
import sys, os, itertools, operator

# import PIL as the image loader
import PIL.Image


def from_file(filepath, **georef):

    def check_world_file(filepath):
        worldfilepath = None
        
        # try to find worldfile
        dir, filename_and_ext = os.path.split(filepath)
        filename, extension = os.path.splitext(filename_and_ext)
        dir_and_filename = os.path.join(dir, filename)
        
        # first check generic .wld extension
        if os.path.lexists(dir_and_filename + ".wld"):
            worldfilepath = dir_and_filename + ".wld"
            
        # if not, check filetype-specific world file extensions
        else:
            # get filetype-specific world file extension
            if extension in ("tif","tiff","geotiff"):
                extension = ".tfw"
            elif extension in ("jpg","jpeg"):
                extension = ".jgw"
            elif extension == "png":
                extension = ".pgw"
            elif extension == "bmp":
                extension = ".bpw"
            elif extension == "gif":
                extension = ".gfw"
            else:
                return None
            # check if exists
            if os.path.lexists(dir_and_filename + extension):
                worldfilepath = dir_and_filename + extension

        # then return contents if file found
        if worldfilepath:
            with open(worldfilepath) as worldfile:
                # note that the params are arranged slightly differently
                # ...in the world file from the usual affine a,b,c,d,e,f
                # ...so remember to rearrange their sequence later
                xscale,yskew,xskew,yscale,xoff,yoff = worldfile.read().split()
            return [xscale,yskew,xskew,yscale,xoff,yoff]

    if filepath.lower().endswith((".asc",".ascii")):
        georef_orig = georef.copy()
        
        with open(filepath) as tempfile:
            ### Step 1: check header for file georef
            georef = dict()
            def _nextheader(headername=None, force2length=True):
                "returns a two-list of headername and headervalue"
                nextline = False
                while not nextline:
                    nextline = tempfile.readline().strip()
                nextline = nextline.split()
                if force2length:
                    if len(nextline) != 2:
                        raise Exception("Each header line must contain exactly two elements")
                if headername:
                    if nextline[0].lower() != headername:
                        raise Exception("The required headername was not found: %s instead of %s"%(nextline[0].lower(),headername))
                return nextline
            
            # dimensions
            cols = int(_nextheader(headername="ncols")[1])
            rows = int(_nextheader(headername="nrows")[1])
            
            # x/y origin
            _next = _nextheader()
            if _next[0].lower() in ("xllcenter","xllcorner"):
                xorig = float(_next[1])
                xorigtype = _next[0].lower()
            _next = _nextheader()
            if _next[0].lower() in ("yllcenter","yllcorner"):
                yorig = float(_next[1])
                yorigtype = _next[0].lower()
            georef["xy_cell"] = (0, rows)
            georef["xy_geo"] = (xorig, yorig)
            if "corner" in xorigtype and "corner" in yorigtype:
                georef["cell_anchor"] = "sw"
            elif "corner" in xorigtype:
                georef["cell_anchor"] = "w"
            elif "corner" in yorigtype:
                georef["cell_anchor"] = "s"
            else:
                georef["cell_anchor"] = "center"
            
            # cellsize
            cellsize = float(_nextheader(headername="cellsize")[1])
            georef["cellwidth"] = cellsize
            georef["cellheight"] = cellsize
            
            # nodata
            prevline = tempfile.tell()
            _next = _nextheader(force2length=False)
            if _next[0].lower() == "nodata_value":
                nodata = float(_next[1])
            else:
                # nodata header missing, so set to default and go back to previous header line
                nodata = -9999.0
                tempfile.seek(prevline)
            
            ### Step 2: read data into lists
            # make sure filereading is set to first data row (in case there are spaces or gaps in between header and data)
            nextline = False
            while not nextline:
                prevline = tempfile.tell()
                nextline = tempfile.readline().strip()
            tempfile.seek(prevline)
            # collect flat list of cells instead of rows (because according to the ASCII format, the rows in the grid could be but aren't necessarily organized into separate lines)
            data = []
            for line in tempfile.readlines():
                data.extend(float(cell) for cell in line.split())
            # reshape values to correspond with row lists, and flatten again
            def grouper(iterable, n):
                args = [iter(iterable)] * n
                return itertools.izip(*args)
            reshaped = itertools.izip(*grouper(data, cols))
            data = [cell for row in reshaped for cell in row]

        georef = dict()

        # Build geotransform
        try:
            # first try manual override georef options
            georef["affine"] = compute_affine(**georef_orig)
        except:
            # worldfile geotransform takes priority over file params
            transform_coeffs = check_world_file(filepath)
            if transform_coeffs:
                # rearrange the world file param sequence to match affine transform
                xscale,yskew,xskew,yscale,xoff,yoff = transform_coeffs
                georef["affine"] = xscale,xskew,xoff,yskew,yscale,yoff
            else:
                # finally try file georef params
                try:
                    georef["affine"] = compute_affine(**georef)
                except:
                    raise Exception("Couldn't find the manual georef options, world file, or file georef parameters needed to position the image in space")

        # Read coordinate ref system
        # esri ascii doesnt have any crs so assume default
        crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

        # Nodata value
        nodataval = nodata
        
        # load the data as an image
        tempfile.close()
        img = PIL.Image.new("F", (rows, cols))
        img.putdata(data=data)
        # make a single-band tuple
        bands = [img]

        return georef, nodataval, bands, crs

    elif filepath.lower().endswith((".tif",".tiff",".geotiff")):
        main_img = PIL.Image.open(filepath)
        raw_tags = dict(main_img.tag.items())
        
        def read_georef(raw_tags):
            # check tag definitions here
            info = dict()
            if raw_tags.has_key(1025):
                # GTRasterTypeGeoKey, aka midpoint pixels vs topleft area pixels
                if raw_tags.get(1025) == (1,):
                    # is area
                    info["cell_anchor"] = "center"
                elif raw_tags.get(1025) == (2,):
                    # is point
                    info["cell_anchor"] = "nw"
            if raw_tags.has_key(34264):
                # ModelTransformationTag, aka 4x4 transform coeffs...
                [a,b,c,d,
                 e,f,g,h,
                 i,j,k,l,
                 m,n,o,p] = raw_tags.get(34264)
                # But we don't want to meddle with 3-D transforms,
                # ...so for now only get the 2-D affine parameters
                xscale,xskew,xoff = a,b,d
                yskew,yscale,yoff = e,f,h
                info.update(xscale=xscale,
                            xskew=xskew,
                            xoffset=xoff,
                            yskew=yskew,
                            yscale=yscale,
                            yoffset=yoff)
            else:
                if raw_tags.has_key(33922):
                    # ModelTiepointTag
                    x, y, z, geo_x, geo_y, geo_z = raw_tags.get(33922)
                    info["xy_cell"] = x,y
                    info["xy_geo"] = geo_x,geo_y
                if raw_tags.has_key(33550):
                    # ModelPixelScaleTag
                    scalex,scaley,scalez = raw_tags.get(33550)
                    info["cellwidth"] = scalex
                    info["cellheight"] = -scaley # note: cellheight must be inversed because geotiff has a reversed y-axis (ie 0,0 is in upperleft corner)
            return info

        def read_nodata(raw_tags):
            nodataval = raw_tags.get(42113)
            if nodataval:
                try:
                    float(nodataval) # make sure is possible to make into nr
                    nodataval = eval(nodataval) # eval from string to nr
                    return nodataval
                except:
                    pass

        def read_crs(raw_tags):
            crs = dict()
            if raw_tags.get(34735):
                # GeoKeyDirectoryTag
                crs["proj_params"] = raw_tags.get(34735)
            if raw_tags.get(34737):
                # GeoAsciiParamsTag
                crs["proj_name"] = raw_tags.get(34737)
            return crs

        # read geotiff georef tags
        georef_orig = georef.copy()
        try:
            # use georef from file tags
            georef = read_georef(raw_tags)
            # override with manual georef options
            georef.update(georef_orig)
            georef["affine"] = compute_affine(**georef)
        except:
            # if no geotiff tag info look for world file transform coefficients
            transform_coeffs = check_world_file(filepath)
            if transform_coeffs:
                # rearrange the world file param sequence to match affine transform
                [xscale,yskew,xskew,yscale,xoff,yoff] = transform_coeffs
                georef["affine"] = [xscale,xskew,xoff,yskew,yscale,yoff]
            else:
                raise Exception("Couldn't find any georef options, geotiff tags, or world file needed to position the image in space")

        # read nodata
        nodataval = read_nodata(raw_tags)

        # group image bands into band tuples
        bands = [im for im in main_img.split()]

        # read coordinate ref system
        crs = read_crs(raw_tags)

        return georef, nodataval, bands, crs

    elif filepath.lower().endswith((".jpg",".jpeg",".png",".bmp",".gif")):
        
        # pure image, so needs either manual georef args, or a world file
        main_img = PIL.Image.open(filepath)
        try:
            georef["affine"] = compute_affine(**georef)
        
        except:
            transform_coeffs = check_world_file(filepath)
            if transform_coeffs:
                # rearrange the param sequence to match affine transform
                [xscale,yskew,xskew,yscale,xoff,yoff] = transform_coeffs
                georef["affine"] = [xscale,xskew,xoff,yskew,yscale,yoff]
            else:
                raise Exception("Couldn't find the world file nor the manual georef options needed to position the image in space")
                
        # group image bands into band tuples
        bands = [im for im in main_img.split()]

        # nodataval
        nodataval = None

        # read crs
        # normal images have no crs, so just assume default crs
        crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

        return georef, nodataval, bands, crs

    elif filepath.lower().endswith(".ncf"):
        # netcdf format files
        # should be simple enough with the struct and array.array modules
        # to read the binary data
        # see file structure at www.unidata.ucar.edu/software/netcdf/docs/netcdf/Classic-Format-Spec.html

        # ALSO, once going over to class based reader,
        # use fast memory views to access data, see see http://eli.thegreenplace.net/2011/11/28/less-copies-in-python-with-the-buffer-protocol-and-memoryviews
        #
        # example:
        # fileobj = open("some/path.ncf", "rb")
        # fileobj.seek(someoffset_tothedatawewant)
        # buff = buffer(struct.unpack(fileobj.read(someamount)))
        # fast_gridvalues = memoryview(buff)
        # return fast_gridvalues  # allows fast indexing and iterating without creating copies

        # OR more relevant when reading:
        # buf = bytearray() or array.array() # empty holders of precalculated size
        # mem = memoryview(buf)
        # f.readinto(mem)

        # ALTERN, just use:
        # grid = array.fromfile(fileobj, chunksize)
        # return memoryview(grid)
        # ...
        pass 

    elif filepath.lower().endswith(".bil"):
        raise Exception("Not yet implemented")

    elif filepath.lower().endswith(".adf"):
        # arcinfo raster: http://support.esri.com/en/knowledgebase/techarticles/detail/30616
        raise Exception("Not yet implemented")

    elif filepath.lower().endswith(".txt"):
        # cell by cell table format
        with open(filepath) as reader:
            nodataval = georef.pop("nodataval", None)
            crs = georef.pop("crs", None)
            
            fields = georef.pop("fields", None)
            if not fields:
                fields = next(reader).split()

            delimiter = georef.pop("delimiter", None)

            xfield,yfield = georef.pop("xfield", None),georef.pop("yfield", None)
            colfield,rowfield = georef.pop("colfield", None),georef.pop("rowfield", None)
            
            if xfield and yfield:
                
                lines = [line.split(delimiter) for line in reader]
                xfieldindex, yfieldindex = fields.index(xfield), fields.index(yfield)

                valuefield = georef.pop("valuefield", None)
                if not valuefield:
                    raise Exception("Valuefield must be specified")
                valuefieldindex = fields.index(valuefield)

                bbox = georef.get("bbox")
                if not bbox:
                    xs,ys = [line[xfieldindex] for line in lines],[line[yfieldindex] for line in lines]
                    bbox = min(xs),min(ys),max(xs),max(ys)
                    georef["bbox"] = bbox

                width,height = georef.get("width"),georef.get("height")
                if not (width and height):
                    # TODO: how to auto figure out from data...
                    pass

                georef["affine"] = compute_affine(**georef)

                firstval = lines[0][valuefieldindex]
                if firstval.isdigit():
                    cast = lambda v: int(float(v))
                    mode = "int32"
                elif firstval.replace('.','').isdigit():
                    cast = lambda v: float(v)
                    mode = "float32"

                # slight cheating to easily calculate col and row
                from .data import RasterData
                temprast = RasterData(mode=mode, **georef)
                band = temprast.add_band(nodataval=nodataval)
                for line in lines:
                    x,y = float(line[xfieldindex]), float(line[yfieldindex])
                    col,row = temprast.geo_to_cell(x,y)
                    val = cast(line[valuefieldindex])
                    band.set(col,row,val)

                band = band.img

                return georef, nodataval, [band], crs

            elif colfield and rowfield:
                
                lines = [line.split(delimiter) for line in reader]
                colfieldindex, rowfieldindex = fields.index(colfield), fields.index(rowfield)

                valuefield = georef.pop("valuefield", None)
                if not valuefield:
                    raise Exception("Valuefield must be specified")
                valuefieldindex = fields.index(valuefield)

                width,height = georef.get("width"),georef.get("height")
                if not (width and height):
                    width,height = max((line[colfieldindex] for line in lines)), max((line[rowfieldindex] for line in lines))
                    georef.update(width=width, height=height)

                georef["affine"] = compute_affine(**georef)

                firstval = lines[0][valuefieldindex]
                if firstval.isdigit():
                    band = PIL.Image.new("I", (width,height), nodataval)
                    cast = lambda v: int(float(v))
                elif firstval.replace('.','').isdigit():
                    band = PIL.Image.new("F", (width,height), nodataval)
                    cast = lambda v: float(v)

                pixelaccess = band.load()
                for line in lines:
                    x,y = line[colfieldindex], line[rowfieldindex]
                    val = cast(line[valuefieldindex])
                    pixelaccess[x,y] = val

                return georef, nodataval, [band], crs

            else:
                raise Exception("Either xfield and yfield or colfield and rowfield must be specified to figure out where each cell belongs")
    
    else:

        raise Exception("Could not create a raster from the given filepath: the filetype extension is either missing or not supported")


def from_lists(data, nodataval=-9999.0, cell_anchor="center", **geoargs):
    raise Exception("Not yet implemented")


def from_image(image, nodataval=-9999.0, crs=None, **georef):

    if "affine" in georef:
        pass
    else:
        georef["affine"] = compute_affine(**georef)

    if not crs:
        crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

    bands = [im for im in image.split()]
    
    return georef, nodataval, bands, crs
        
def new(nodataval=-9999.0, crs=None, **georef):

    if "affine" in georef:
        pass
    else:
        georef["affine"] = compute_affine(**georef)

    if not crs:
        crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    
    bands = []
        
    return georef, nodataval, bands, crs

def compute_affine(xy_cell=None, xy_geo=None, cellwidth=None, cellheight=None,
                   width=None, height=None, bbox=None,
                   xscale=None, yscale=None, xskew=0, yskew=0,
                   xoffset=None, yoffset=None,
                   cell_anchor="center"):

    # get scale values
    if not xscale:
        if cellwidth:
            xscale = cellwidth
        elif bbox and width:
            xwidth = bbox[2]-bbox[0]
            xscale = xwidth / float(width+1) # +1 is to account for the two half pixels padding of bbox
    if not yscale:
        if cellheight:
            yscale = cellheight
        elif bbox and height:
            yheight = bbox[3]-bbox[1]
            yscale = yheight / float(height+1) # +1 is to account for the two half pixels padding of bbox

    # bbox is only used manually by user and should include the corners (+- half cellsize)
    # need to remove this padding to get it right
    if bbox:
        x1,y1,x2,y2 = bbox
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
        bbox = x1,y1,x2,y2

    # get skew values from bbox if not specified
    # ...
    
    # get offset values
    if any((xoffset == None, yoffset == None)):
        if (xy_cell and xy_geo):
            xcell,ycell = xy_cell
            xgeo,ygeo = xy_geo
            xoffset,yoffset = xgeo - xcell, ygeo - ycell
        elif bbox:
            xoffset,yoffset = bbox[0],bbox[1]

    # test if enought information to set affine
    if all((opt != None for opt in [xscale,yscale,xskew,yskew,xoffset,yoffset])):
        pass

    else:
        raise Exception("Georef affine can only be computed if given (xy_cell,xy_geo,cellwidth,cellheight) or (width,height,bbox) or ...")

    # offset cell anchor to the center # NOT YET TESTED
    if cell_anchor == "center":
        pass
    elif "n" in cell_anchor:
        yoffset -= cellheight/2.0
    elif "s" in cell_anchor:
        yoffset += cellheight/2.0
    elif "w" in cell_anchor:
        xoffset -= cellwidth/2.0
    elif "e" in cell_anchor:
        xoffset += cellwidth/2.0

    transform_coeffs = [xscale, xskew, xoffset, yskew, yscale, yoffset]
    return transform_coeffs

        
