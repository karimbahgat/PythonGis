
# import internals
import sys, os, itertools, operator

# import PIL as the image loader
import PIL.Image


def from_file(filepath):

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
        with open(filepath) as tempfile:
            ### Step 1: check header for file info
            info = dict()
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
            info["xy_cell"] = (0, rows)
            info["xy_geo"] = (xorig, yorig)
            if "corner" in xorigtype and "corner" in yorigtype:
                info["cell_anchor"] = "sw"
            elif "corner" in xorigtype:
                info["cell_anchor"] = "w"
            elif "corner" in yorigtype:
                info["cell_anchor"] = "s"
            else:
                info["cell_anchor"] = "center"
            
            # cellsize
            cellsize = float(_nextheader(headername="cellsize")[1])
            info["cellwidth"] = cellsize
            info["cellheight"] = cellsize
            
            # nodata
            prevline = tempfile.tell()
            _next = _nextheader(force2length=False)
            if _next[0].lower() == "nodata_value":
                nodata = float(_next[1])
            else:
                # nodata header missing, so set to default and go back to previous header line
                nodata = -9999.0
                tempfile.seek(prevline)
            info["nodata_value"] = nodata
            
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

            ### Step 3: Read worldfile geotransform
            transform_coeffs = check_world_file(filepath)
            if transform_coeffs:
                # rearrange the world file param sequence to match affine transform
                xscale,yskew,xskew,yscale,xoff,yoff = transform_coeffs
                info["transform_coeffs"] = xscale,xskew,xoff,yskew,yscale,yoff
            else:
                raise Exception("Couldn't find the world file needed to position the image in space")

            ### Step 4: Read coordinate ref system
            # esri ascii doesnt have any crs so assume default
            crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
            
        # load the data as an image
        tempfile.close()
        img = PIL.Image.new("F", (rows, cols))
        img.putdata(data=data)
        # create the cell access object
        cells = img.load()
        # make a single-band tuple
        bands = [(img,cells)]

        return info, bands, crs

    elif filepath.lower().endswith((".tif",".tiff",".geotiff")):
        main_img = PIL.Image.open(filepath)
        raw_tags = dict(main_img.tag.items())
        
        def process_metadata(raw_tags):
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
                a,b,c,d,
                e,f,g,h,
                i,j,k,l,
                m,n,o,p = raw_tags.get(34264)
                # But we don't want to meddle with 3-D transforms,
                # ...so for now only get the 2-D affine parameters
                xscale,xskew,xoff = a,b,d
                yskew,yscale,yoff = e,f,h
                info["transform_coeffs"] = xscale,xskew,xoff,yskew,yscale,yoff
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
            if raw_tags.get(42113):
                info["nodata_value"] = eval(raw_tags.get(42113)) # eval from string to nr
            return info

        def read_crs(raw_tags):
            crs = dict()
            if raw_tags.get(34735):
                # GeoKeyDirectoryTag
                crs["proj_params"] = raw_tags.get(34735)
            if raw_tags.get(34737):
                # GeoAsciiParamsTag
                crs["proj_name"] = raw_tags.get(34737)
            return crs          

        # read geotiff metadata tags
        info = process_metadata(raw_tags)

        # if no geotiff tag info look for world file transform coefficients
        if len(info) <= 1 and not info.get("transform_coeffs"):
            transform_coeffs = check_world_file(filepath)
            if transform_coeffs:
                # rearrange the world file param sequence to match affine transform
                [xscale,yskew,xskew,yscale,xoff,yoff] = transform_coeffs
                info["transform_coeffs"] = [xscale,xskew,xoff,yskew,yscale,yoff]
            else:
                raise Exception("Couldn't find any geotiff tags or world file needed to position the image in space")

        # group image bands and pixel access into band tuples
        bands = []
        for img in main_img.split():
            cells = img.load()
            bands.append((img,cells))

        # read coordinate ref system
        crs = read_crs(raw_tags)

        return info, bands, crs

    elif filepath.lower().endswith((".jpg",".jpeg",".png",".bmp",".gif")):
        
        # pure image, so only read if has a world file
        transform_coeffs = check_world_file(filepath)
        if transform_coeffs:
            # rearrange the param sequence to match affine transform
            [xscale,yskew,xskew,yscale,xoff,yoff] = transform_coeffs
            info["transform_coeffs"] = [xscale,xskew,xoff,yskew,yscale,yoff]
            
            # group image bands and pixel access into band tuples
            bands = []
            for img in main_img.split():
                cells = img.load()
                bands.append((img,cells))

            # read crs
            # normal images have no crs, so just assume default crs
            crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

            return info, bands, crs

        else:
            raise Exception("Couldn't find the world file needed to position the image in space")
    
    else:

        raise Exception("Could not create a raster from the given filepath: the filetype extension is either missing or not supported")


def from_lists(data, nodata_value=-9999.0, cell_anchor="center", **geoargs):
    pass


def from_image(image, nodata_value=-9999.0, cell_anchor="center", **geoargs):
    size = image.size
    print geoargs
    info = dict([(key,val) for key,val in geoargs.iteritems()
                 if key in ("xy_cell","xy_geo","cellwidth",
                            "cellheight","transform_coeffs") ])
    
    if len(info) <= 3 and not info.get("transform_coeffs"):
        raise Exception("To make a new raster from scratch, you must specify either all of xy_cell, xy_geo, cellwidth, cellheight, or the transform coefficients")

    info["nodata_value"] = nodata_value
    info["cell_anchor"] = cell_anchor

    crs = geoargs.get("crs", "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")

    grids = []
    cells = image.load()
    grids.append((image, cells))

    return info, grids, crs
        
def new(width, height, nodata_value=-9999.0, bands=1, cell_anchor="center", **geoargs):
    size = (width, height)
    info = dict([(key,val) for key,val in geoargs.iteritems()
                 if key in ("xy_cell","xy_geo","cellwidth",
                            "cellheight","transform_coeffs") ])
    
    if len(info) <= 3 and not info.get("transform_coeffs"):
        raise Exception("To make a new raster from scratch, you must specify either all of xy_cell, xy_geo, cellwidth, cellheight, or the transform coefficients")

    info["nodata_value"] = nodata_value
    info["cell_anchor"] = cell_anchor

    crs = geoargs.get("crs", "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    
    grids = []
    for _ in range(bands):
        img = PIL.Image.new("F", size, float(nodata_value))
        cells = img.load()
        grids.append((img, cells))
        
    return info, grids, crs


        
