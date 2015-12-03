
# import builtins
import sys, os, itertools, operator

# import internals
from . import loader
from . import saver

# import PIL as the data container
import PIL.Image, PIL.ImageMath


class Cell:
    def __init__(self, band, col, row):
        self.band = band
        self.col, self.row = col, row

    def __repr__(self):
        return "Cell(col=%s, row=%s, value=%s)" %(self.col, self.row, self.value)

    @property
    def value(self):
        if not self.band._pixelaccess:
            self.band._pixelaccess = self.img.load()
        return self.band._pixelaccess[self.col, self.row]

    @property
    def neighbours(self):
        nw = Cell(self.band, self.col - 1, self.row + 1)
        n = Cell(self.band, self.col, self.row + 1)
        ne = Cell(self.band, self.col + 1, self.row + 1)
        e = Cell(self.band, self.col + 1, self.row)
        se = Cell(self.band, self.col + 1, self.row - 1)
        s = Cell(self.band, self.col, self.row - 1)
        sw = Cell(self.band, self.col - 1, self.row - 1)
        w = Cell(self.band, self.col - 1, self.row)
        return [nw,n,ne,e,se,s,sw,w]
        

class Band:
    def __init__(self, img, nodataval=None):
        self.img = img
        self.nodataval = nodataval
        self._pixelaccess = None

    def __iter__(self):
        width,height = self.img.size
        for row in range(height):
            for col in range(width):
                yield Cell(self,col,row)
            
    @property
    def width(self):
        return self.img.size[0]

    @property
    def height(self):
        return self.img.size[1]

    @property
    def mode(self):
        return self.img.mode

    def get(self, col, row):
        return Cell(self, col, row)

    def set(self, col, row, value):
        if not self._pixelaccess:
            self._pixelaccess = self.img.load()
        self._pixelaccess[col,row] = value

    @getter
    def mask(self):
        if hasattr(self, "_cached_mask"):
            return self._cached_mask

        else:
            nodata = self.nodataval
            if nodata != None:
                # mask out nodata
                if self.mode in ("F","I"):
                    # if 32bit float or int values, need to manually check each cell
                    mask = PIL.Image.new("1", (self.width, self.height), 1)
                    maskpx = mask.load()
                    for col in xrange(self.width):
                        for row in xrange(self.height):
                            if self._pixelaccess[col,row] == nodata:
                                maskpx[col,row] = 0
                else:
                    # use the much faster point method
                    mask = self.img.point(lambda px: 1 if px != nodata else 0, "1")
            else:
                # EVEN IF NO NODATA, NEED TO CREATE ORIGINAL MASK,
                # TO PREVENT INFINITE OUTSIDE BORDER AFTER GEOTRANSFORM
                mask = PIL.Image.new("1", self.img.size, 1)
            self._cached_mask = mask
            return self._cached_mask

    @setter
    def mask(self, value):
        self._cached_mask = value

    def copy(self):
        img = self.img.copy()
        return Band(img)


class RasterData:
    def __init__(self, filepath=None, data=None, image=None, **kwargs):
        self.filepath = filepath
        
        if filepath:
            georef, nodataval, bands, crs = loader.from_file(filepath)
        elif data:
            georef, nodataval, bands, crs = loader.from_lists(data, **kwargs)
        elif image:
            georef, nodataval, bands, crs = loader.from_image(image, **kwargs)
        else:
            georef, nodataval, bands, crs = loader.new(**kwargs)

        self.bands = [Band(img, nodataval=nodataval) for img in bands]

        self.crs = crs

        self.set_geotransform(**georef["affine"])

    def __len__(self):
        return len(self.bands)
    
    def __iter__(self):
        for band in self.bands:
            yield band
            
    @property
    def width(self):
        return self.bands[0].img.size[0]

    @property
    def height(self):
        return self.bands[0].img.size[1]

    @property
    def mode(self):
        return self.bands[0].img.mode

    @property
    def nodatavals(self):
        return [band.nodataval for band in self.bands]

    @property
    def meta(self):
        metadict = dict(bands=len(self),
                        mode=self.mode,
                        width=self.width,
                        height=self.height,
                        nodatavals=self.nodatavals,
                        affine=self.affine)
        return metadict

    @property
    def bbox(self):
        # get corner coordinates of raster
        xleft_coord,ytop_coord = self.cell_to_geo(0,0)
        xright_coord,ybottom_coord = self.cell_to_geo(self.width, self.height)
        return [xleft_coord,ytop_coord,xright_coord,ybottom_coord]

    def copy(self):
        new = RasterData(width=self.width, height=self.height, **self.info)
        new.bands = [band.copy() for band in self.bands]
        new._cached_mask = self.mask
        return new

    def add_band(self):
        pass # ....

    def set_geotransform(self, **georef):
        
        # get coefficients needed to convert from raster to geographic space
        if "affine" in georef:
            [xscale, xskew, xoffset,
             yskew, yscale, yoffset] = info["affine"]
        else:
            xcell,ycell = georef["xy_cell"]
            xgeo,ygeo = georef["xy_geo"]
            xoffset,yoffset = xgeo - xcell, ygeo - ycell
            xscale,yscale = georef["cellwidth"], georef["cellheight"] 
            xskew,yskew = 0,0

        # offset cell anchor to the center # NOT YET TESTED
        cell_anchor = georef["cell_anchor"]
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
            
        self.affine = [xscale, xskew, xoffset, yskew, yscale, yoffset]

        # and the inverse coefficients to go from geographic space to raster
        # taken from Sean Gillies' "affine.py"
        a,b,c,d,e,f = self.affine
        det = a*e - b*d
        if det != 0:
            idet = 1 / float(det)
            ra = e * idet
            rb = -b * idet
            rd = -d * idet
            re = a * idet
            a,b,c,d,e,f = (ra, rb, -c*ra - f*rb,
                           rd, re, -c*rd - f*re)
            self.inv_affine = a,b,c,d,e,f
        else:
            raise Exception("Error with the transform matrix, \
                            a raster should not collapse upon itself")

    def cell_to_geo(self, column, row):
        [xscale, xskew, xoffset, yskew, yscale, yoffset] = self.affine
        x, y = column, row
        x_coord = x*xscale + y*xskew + xoffset
        y_coord = x*yskew + y*yscale + yoffset
        return x_coord, y_coord

    def geo_to_cell(self, x, y, fraction=False):
        [xscale, xskew, xoffset, yskew, yscale, yoffset] = self.inv_affine
        column = x*xscale + y*xskew + xoffset
        row = x*yskew + y*yscale + yoffset
        if not fraction:
            # round to nearest cell
            column,row = int(round(column)), int(round(row))
        return column,row

    @getter
    def mask(self):
        if hasattr(self, "_cached_mask"):
            return self._cached_mask

        else:
            if len(self) == 1:
                mask = self.bands[0].mask
            elif len(self) > 1:
                # mask out where all bands have nodata value
                masks_namedict = dict([("mask%i"%i, band.mask) for i,band in enumerate(band) ])
                expr = " & ".join(masks_namedict.keys())
                mask = PIL.ImageMath.eval(expr, **masks_namedict).convert("1")

            self._cached_mask = mask
            return self._cached_mask

    @setter
    def mask(self, value):
        self._cached_mask = value

    def positioned(self, width, height, coordspace_bbox):
        # GET COORDS OF ALL 4 VIEW SCREEN CORNERS
        xleft,ytop,xright,ybottom = coordspace_bbox
        viewcorners = [(xleft,ytop), (xleft,ybottom), (xright,ybottom), (xright,ytop)]
        
        # FIND PIXEL LOCS OF ALL THESE COORDS ON THE RASTER
        viewcorners_pixels = [self.geo_to_cell(*point, fraction=True) for point in viewcorners]

        # ON RASTER, PERFORM QUAD TRANSFORM
        #(FROM VIEW SCREEN COORD CORNERS IN PIXELS TO RASTER COORD CORNERS IN PIXELS)
        flattened = [xory for point in viewcorners_pixels for xory in point]
        newraster = self.copy()

        # make mask over
        self.mask = self.mask.transform((width,height), PIL.Image.QUAD,
                            flattened, resample=PIL.Image.NEAREST)
        
        for band in newraster.bands:
            datatrans = band.img.transform((width,height), PIL.Image.QUAD,
                                flattened, resample=PIL.Image.NEAREST)
            trans = PIL.Image.new(datatrans.mode, datatrans.size)
            trans.paste(datatrans, (0,0), masktrans)
            # store image
            band.img = trans

        return newraster 

    def save(self, filepath):
        saver.to_file(self.bands, self.info, filepath)



        
