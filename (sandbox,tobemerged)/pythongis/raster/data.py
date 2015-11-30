import sys, os, itertools, operator

from . import loader
from . import saver

import PIL.Image


class Cell:
    def __init__(self, grid, x, y):
        self.grid = grid
        self.x, self.y = x, y

    def __repr__(self):
        return "Cell(x=%s, y=%s, value=%s)" %(self.x, self.y, self.value)

    @property
    def value(self):
        return self.grid.cells[self.x, self.y]

    @property
    def neighbours(self):
        nw = Cell(self.grid, self.x - 1, self.y + 1)
        n = Cell(self.grid, self.x, self.y + 1)
        ne = Cell(self.grid, self.x + 1, self.y + 1)
        e = Cell(self.grid, self.x + 1, self.y)
        se = Cell(self.grid, self.x + 1, self.y - 1)
        s = Cell(self.grid, self.x, self.y - 1)
        sw = Cell(self.grid, self.x - 1, self.y - 1)
        w = Cell(self.grid, self.x - 1, self.y)
        return [nw,n,ne,e,se,s,sw,w]
        

class Grid:
    def __init__(self, img, cells):
        self.img = img
        self.cells = cells

    def __iter__(self):
        width,height = self.img.size
        for y in range(height):
            for x in range(width):
                yield Cell(self,x,y)
            
    def get(self, x, y):
        return Cell(self, x, y)

    def set(self, x, y, value):
        self.cells[x,y] = value

    def copy(self):
        img = self.img.copy()
        cells = img.load()
        return Grid(img, cells)


class Raster:
    def __init__(self, filepath=None, data=None, image=None, **kwargs):
        self.filepath = filepath
        
        if filepath:
            info, grids, crs = loader.from_file(filepath)
        elif data:
            info, grids, crs = loader.from_lists(data, **kwargs)
        elif image:
            info, grids, crs = loader.from_image(image, **kwargs)
        else:
            info, grids, crs = loader.new(**kwargs)

        print info
        self.grids = [Grid(img,cells) for img,cells in grids]

        self.info = info

        self.crs = crs

        self.update_geotransform()
    
    def __iter__(self):
        for grid in self.grids:
            yield grid
            
    @property
    def width(self):
        return self.grids[0].img.size[0]

    @property
    def height(self):
        return self.grids[0].img.size[1]

    @property
    def bbox(self):
        # get corner coordinates of raster
        xleft_coord,ytop_coord = self.cell_to_geo(0,0)
        xright_coord,ybottom_coord = self.cell_to_geo(self.width, self.height)
        return [xleft_coord,ytop_coord,xright_coord,ybottom_coord]

    def copy(self):
        new = Raster(width=self.width, height=self.height, **self.info)
        new.grids = [grid.copy() for grid in self.grids]
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
        # round to nearest cell
        if not fraction:
            column,row = int(round(column)), int(round(row))
        return column,row

    @property
    def mask(self):
        if hasattr(self, "_cached_mask"):
            return self._cached_mask

        else:
            print "MASK"
            nodata = self.info.get("nodata_value")
            if nodata != None:
                # mask out nodata
                if self.grids[0].img.mode in ("F","I"):
                    # if 32bit float or int values, need to manually check each cell
                    mask = PIL.Image.new("1", (self.width, self.height), 1)
                    px = mask.load()
                    for x in xrange(self.width):
                        for y in xrange(self.height):
                            value = (band.cells[x,y] for band in self.grids)
                            # mask out only where all bands have nodata value
                            if all((val == nodata for val in value)):
                                px[x,y] = 0
                else:
                    # use the much faster point method
                    masks = []
                    for band in self.grids:
                        print "MODE",band.img.mode
                        mask = band.img.point(lambda px: 1 if px != nodata else 0, "1")
                        masks.append(mask)
                    # mask out where all bands have nodata value
                    masks_namedict = dict([("mask%i"%i, mask) for i,mask in enumerate(masks) ])
                    expr = " & ".join(masks_namedict.keys())
                    print expr, masks_namedict
                    mask = PIL.ImageMath.eval(expr, **masks_namedict).convert("1")
                    print mask.mode
            else:
                # EVEN IF NO NODATA, NEED TO CREATE ORIGINAL MASK,
                # TO PREVENT INFINITE OUTSIDE BORDER AFTER GEOTRANSFORM
                nodata = 0
                mask = PIL.Image.new("1", self.grids[0].img.size, 1)
            self._cached_mask = mask
            return self._cached_mask

    def positioned(self, width, height, coordspace_bbox):
        # GET COORDS OF ALL 4 VIEW SCREEN CORNERS
        xleft,ytop,xright,ybottom = coordspace_bbox
        viewcorners = [(xleft,ytop), (xleft,ybottom), (xright,ybottom), (xright,ytop)]
        
        # FIND PIXEL LOCS OF ALL THESE COORDS ON THE RASTER
        viewcorners_pixels = [self.geo_to_cell(*point, fraction=True) for point in viewcorners]
        print ("wobaba", width, height)
        print viewcorners_pixels
        print "---"

        # ON RASTER, PERFORM QUAD TRANSFORM
        #(FROM VIEW SCREEN COORD CORNERS IN PIXELS TO RASTER COORD CORNERS IN PIXELS)
        flattened = [xory for point in viewcorners_pixels for xory in point]
        newraster = self.copy()

        #self.update_mask()
        mask = self.mask
        #mask = mask.convert("1")

        # make mask over 
        masktrans = mask.transform((width,height), PIL.Image.QUAD,
                            flattened, resample=PIL.Image.NEAREST)
        
        for grid in newraster.grids:            
            datatrans = grid.img.transform((width,height), PIL.Image.QUAD,
                                flattened, resample=PIL.Image.NEAREST)
            trans = PIL.Image.new(datatrans.mode, datatrans.size)
            trans.paste(datatrans, (0,0), masktrans)
            #trans.save("trans.png")
            # store image and cells
            grid.img = trans
            # print "wiki",width,height,grid.img,grid.img.getbbox()
            # grid.img.save("testtrans2.png")
            grid.cells = grid.img.load()

        return newraster,masktrans


##        # GET COORDS OF ALL 4 VIEW SCREEN CORNERS
##        xleft,ytop,xright,ybottom = coordspace_bbox
##        viewcorners = [(xleft,ytop), (xleft,ybottom), (xright,ybottom), (xright,ytop)]
##        
##        # FIND PIXEL LOCS OF ALL THESE COORDS ON THE RASTER
##        viewcorners_pixels = [self.geo_to_cell(*point, fraction=True) for point in viewcorners]
##        print viewcorners_pixels
##        print "---"
##
##        # ON RASTER, PERFORM QUAD TRANSFORM
##        #(FROM VIEW SCREEN COORD CORNERS IN PIXELS TO RASTER COORD CORNERS IN PIXELS)
##        flattened = [xory for point in viewcorners_pixels for xory in point]
##        newraster = self.copy()
##        for grid in newraster.grids:
##            grid.img = grid.img.transform((width,height), PIL.Image.QUAD,
##                                flattened, resample=PIL.Image.NEAREST)
##            grid.cells = grid.img.load()
##        return newraster

    def save(self, filepath):
        saver.to_file(self.grids, self.info, filepath)



        
