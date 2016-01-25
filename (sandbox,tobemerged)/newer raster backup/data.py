
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
        return self.band.cells[self.col, self.row]

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
    def __init__(self, img, cells):
        self.img = img
        self.cells = cells

    def __iter__(self):
        width,height = self.img.size
        for row in range(height):
            for col in range(width):
                yield Cell(self,col,row)
            
    def get(self, col, row):
        return Cell(self, col, row)

    def set(self, col, row, value):
        self.cells[col,row] = value

    def copy(self):
        img = self.img.copy()
        cells = img.load()
        return Band(img, cells)


class RasterData:
    def __init__(self, filepath=None, data=None, image=None, **kwargs):
        self.filepath = filepath
        
        if filepath:
            info, bands, crs = loader.from_file(filepath)
        elif data:
            info, bands, crs = loader.from_lists(data, **kwargs)
        elif image:
            info, bands, crs = loader.from_image(image, **kwargs)
        else:
            info, bands, crs = loader.new(**kwargs)

        self.bands = [Band(img,cells) for img,cells in bands]

        self.info = info

        self.crs = crs

        self.update_geotransform()
    
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

    def update_geotransform(self):
        info = self.info
        
        # get coefficients needed to convert from raster to geographic space
        if info.get("transform_coeffs"):
            [xscale, xskew, xoffset,
             yskew, yscale, yoffset] = info["transform_coeffs"]
        else:
            xcell,ycell = info["xy_cell"]
            xgeo,ygeo = info["xy_geo"]
            xoffset,yoffset = xgeo - xcell, ygeo - ycell
            xscale,yscale = info["cellwidth"], info["cellheight"] 
            xskew,yskew = 0,0
        self.transform_coeffs = [xscale, xskew, xoffset, yskew, yscale, yoffset]

        # and the inverse coefficients to go from geographic space to raster
        # taken from Sean Gillies' "affine.py"
        a,b,c,d,e,f = self.transform_coeffs
        det = a*e - b*d
        if det != 0:
            idet = 1 / float(det)
            ra = e * idet
            rb = -b * idet
            rd = -d * idet
            re = a * idet
            a,b,c,d,e,f = (ra, rb, -c*ra - f*rb,
                           rd, re, -c*rd - f*re)
            self.inv_transform_coeffs = a,b,c,d,e,f
        else:
            raise Exception("Error with the transform matrix, \
                            a raster should not collapse upon itself")

    def cell_to_geo(self, column, row):
        [xscale, xskew, xoffset, yskew, yscale, yoffset] = self.transform_coeffs
        x, y = column, row
        x_coord = x*xscale + y*xskew + xoffset
        y_coord = x*yskew + y*yscale + yoffset
        return x_coord, y_coord

    def geo_to_cell(self, x, y, fraction=False):
        [xscale, xskew, xoffset, yskew, yscale, yoffset] = self.inv_transform_coeffs
        column = x*xscale + y*xskew + xoffset
        row = x*yskew + y*yscale + yoffset
        if not fraction:
            # round to nearest cell
            column,row = int(round(column)), int(round(row))
        return column,row

    @property
    def mask(self):
        if hasattr(self, "_cached_mask"):
            return self._cached_mask

        else:
            nodata = self.info.get("nodata_value")
            if nodata != None:
                # mask out nodata
                if self.bands[0].img.mode in ("F","I"):
                    # if 32bit float or int values, need to manually check each cell
                    mask = PIL.Image.new("1", (self.width, self.height), 1)
                    px = mask.load()
                    for col in xrange(self.width):
                        for row in xrange(self.height):
                            value = (band.cells[col,row] for band in self.bands)
                            # mask out only where all bands have nodata value
                            if all((val == nodata for val in value)):
                                px[col,row] = 0
                else:
                    # use the much faster point method
                    masks = []
                    for band in self.bands:
                        mask = band.img.point(lambda px: 1 if px != nodata else 0, "1")
                        masks.append(mask)
                    # mask out where all bands have nodata value
                    masks_namedict = dict([("mask%i"%i, mask) for i,mask in enumerate(masks) ])
                    expr = " & ".join(masks_namedict.keys())
                    mask = PIL.ImageMath.eval(expr, **masks_namedict).convert("1")
            else:
                # EVEN IF NO NODATA, NEED TO CREATE ORIGINAL MASK,
                # TO PREVENT INFINITE OUTSIDE BORDER AFTER GEOTRANSFORM
                nodata = 0
                mask = PIL.Image.new("1", self.bands[0].img.size, 1)
            self._cached_mask = mask
            return self._cached_mask

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

        mask = self.mask

        # make mask over 
        masktrans = mask.transform((width,height), PIL.Image.QUAD,
                            flattened, resample=PIL.Image.NEAREST)
        
        for band in newraster.bands:
            datatrans = band.img.transform((width,height), PIL.Image.QUAD,
                                flattened, resample=PIL.Image.NEAREST)
            trans = PIL.Image.new(datatrans.mode, datatrans.size)
            trans.paste(datatrans, (0,0), masktrans)
            # store image and cells
            band.img = trans
            band.cells = band.img.load()

        return newraster,masktrans  # TODO: WHY NOT JUST SET MASKTRANS AS NEWRASTER'S ._cached_mask?

    def save(self, filepath):
        saver.to_file(self.bands, self.info, filepath)



        
