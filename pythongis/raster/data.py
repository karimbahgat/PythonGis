
# import builtins
import sys, os, itertools, operator

# import internals
from . import loader
from . import saver

# import PIL as the data container
import PIL.Image, PIL.ImageMath, PIL.ImageStat


class Cell(object):
    def __init__(self, band, col, row):
        self.band = band
        self.col, self.row = col, row

    def __repr__(self):
        return "Cell(col=%s, row=%s, value=%s)" %(self.col, self.row, self.value)

    @property
    def value(self):
        if not self.band._pixelaccess:
            self.band._pixelaccess = self.band.img.load()
        return self.band._pixelaccess[self.col, self.row]

    @value.setter
    def value(self, newval):
        if not self.band._pixelaccess:
            self.band._pixelaccess = self.band.img.load()
        self.band._pixelaccess[self.col, self.row] = newval

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
        

class Band(object):
    def __init__(self, img=None, mode=None, width=None, height=None, nodataval=-9999):
        """Only used internally, use instead RasterData's .add_band()"""

        if not img:
            if all((mode,width,height)):
                pilmode = rastmode_to_pilmode(mode)
                img = PIL.Image.new(pilmode, (width, height))
            else:
                raise Exception("Mode, width, and height must be specified when creating a new empty band from scratch")
        
        self.img = img

        self.nodataval = nodataval # calls on the setter method
        self._pixelaccess = None
        self._cached_mask = None

    def __iter__(self):
        width,height = self.img.size
        for row in range(height):
            for col in range(width):
                yield Cell(self,col,row)

    def __repr__(self):
        import pprint
        metadict = dict(img=self.img,
                        nodataval=self.nodataval)
        return "Band object:\n" + pprint.pformat(metadict, indent=4)
            
    @property
    def width(self):
        return self.img.size[0]

    @property
    def height(self):
        return self.img.size[1]

    @property
    def mode(self):
        return pilmode_to_rastmode(self.img.mode)

    @property
    def nodataval(self):
        return self._nodataval

    @nodataval.setter
    def nodataval(self, nodataval):
        if nodataval != None:
            if self.mode == "1bit":
                self._nodataval = int(nodataval)
            elif self.mode.startswith("int"):
                self._nodataval = int(nodataval)
            elif self.mode.startswith("float"):
                self._nodataval = float(nodataval)
        else:
            self._nodataval = nodataval

    def get(self, col, row):
        return Cell(self, col, row)

    def set(self, col, row, value):
        if not self._pixelaccess:
            self._pixelaccess = self.img.load()
        self._pixelaccess[col,row] = value

    @property
    def mask(self):
        if self._cached_mask:
            return self._cached_mask

        else:
            nodata = self.nodataval
            if nodata != None:
                # mask out nodata
                mask = self._conditional("val == %s" %nodata)
                
            else:
                # EVEN IF NO NODATA, NEED TO CREATE ORIGINAL MASK,
                # TO PREVENT INFINITE OUTSIDE BORDER AFTER GEOTRANSFORM
                mask = PIL.Image.new("1", self.img.size, 0)
                
            self._cached_mask = mask
            return self._cached_mask

    @mask.setter
    def mask(self, value):
        self._cached_mask = value

    def compute(self, expr):
        """Apply the given expression to recompute all values"""
        # get the mask before changing values
        if self.nodataval != None:
            mask = self.mask

        # change values
        self._compute(expr)

        # use the original nodatamask to set null values again
        if self.nodataval != None:
            self.img.paste(self.nodataval, (0,0), mask)

    def _compute(self, expr):
        """Internal only"""
        try:
            _expr = "convert(%s, '%s')" % (expr, self.img.mode)
            print _expr
            result = PIL.ImageMath.eval(_expr, val=self.img)
            self.img = result
        
        except MemoryError:
            
            if not self._pixelaccess:
                self._pixelaccess = self.img.load()

            # force mode
            if self.mode.startswith(("int","1bit")):
                forcetype = int
            elif self.mode.startswith("float"):
                forcetype = float
                                    
            # force value range
            if self.mode == "1bit":
                forcerange = lambda v: min(max(v,0),1)
            elif self.mode.endswith("8"):
                forcerange = lambda v: min(max(v,0),255)
            else:
                forcerange = lambda v: v
            
            for y in range(self.width):
                for x in range(self.height):
                    val = self._pixelaccess[x,y]
                    newval = eval(expr, {}, {"val":val})
                    self._pixelaccess[x,y] = forcetype(forcerange(newval))

    def recode(self, condition, newval):
        """Change to a new value for those pixels that meet a condition"""
        wheretrue = self._conditional(condition)
        self.img.paste(newval, (0,0), wheretrue)

    def conditional(self, condition):
        """Return a binary band showing where a condition is true"""
        
        result = self._conditional(condition)

        # set conditional to false for pixels covered by nodatamask
        if self.nodataval != None:
            result.paste(0, (0,0), self.mask)

        band = Band(result, self.nodataval)
        return band

    def _conditional(self, condition):
        """Optimized algorithms for testing condition depending on raster type,
        avoids recursion when calling mask"""
        
        try: 
            # note: relational ops < > == != should return only binary mask, but not sure
            _condition = "convert((%s)*255, '1')" % condition
            result = PIL.ImageMath.eval(_condition, val=self.img)
            
            # times binary results with 255 to make a valid mask
            ####result = PIL.ImageMath.eval("convert(val * 255, '1')", val=result)

        except MemoryError:
            result = PIL.Image.new("1", self.img.size, 0)
            resultpixels = result.load()
            
            if not self._pixelaccess:
                self._pixelaccess = self.img.load()

            # Note: eval on many pixels is very slow
            for y in range(self.width):
                for x in range(self.height):
                    val = self._pixelaccess[x,y]
                    if eval(condition, {}, {"val":val}) != False:
                        resultpixels[x,y] = 255
                    else:
                        resultpixels[x,y] = 0

        return result

    def summarystats(self, *stattypes):
        # get all stattypes unless specified

        statsdict = dict()
        
        if self.mode.endswith("8"):
            # PIL.ImageStat only works for modes with values below 255

            # retrieve stats
            valid = self.mask.point(lambda v: 1 if v==0 else 0)
            stats = PIL.ImageStat.Stat(self.img, valid)
            _min,_max = stats.extrema[0]

            print stats.count, stats.sum

            if not stattypes or "count" in stattypes:
                statsdict["count"] = stats.count[0]
            if not stattypes or "sum" in stattypes:
                statsdict["sum"] = stats.sum[0]
            if not stattypes or "mean" in stattypes:
                try: statsdict["mean"] = stats.mean[0]
                except ZeroDivisionError: statsdict["mean"] = None
            if not stattypes or "min" in stattypes:
                statsdict["min"] = _min
            if not stattypes or "max" in stattypes:
                statsdict["max"] = _max
            # some more stats
            # ...

        elif self.mode.endswith(("16","32","1bit")):
            
            try:
                # manually get count of all unique pixelvalues and do math on it
                # but do not include counts of nodataval
                
                nodata = self.nodataval
                def valuecountsgen():
                    return ((cnt,val) for cnt,val in self.img.getcolors(self.width*self.height) if val != nodata)
                
                def _count():
                    return sum((cnt for cnt,val in valuecountsgen()))
                def _sum():
                    return sum((cnt*val for cnt,val in valuecountsgen()))
                def _mean():
                    return _sum()/float(_count())
                def _min():
                    return min((val for cnt,val in valuecountsgen()))
                def _max():
                    return max((val for cnt,val in valuecountsgen()))
                    
                if not stattypes or "count" in stattypes:
                    statsdict["count"] = _count()
                if not stattypes or "sum" in stattypes:
                    statsdict["sum"] = _sum()
                if not stattypes or "mean" in stattypes:
                    statsdict["mean"] = _mean()
                if not stattypes or "min" in stattypes:
                    statsdict["min"] = _min()
                if not stattypes or "max" in stattypes:
                    statsdict["max"] = _max()
                # some more stats
                # ...
                
            except MemoryError:

                # getcolors() resulted in too many values at once
                # so fallback on manual iteration one pixel at a time

                if not self._pixelaccess:
                    self._pixelaccess = self.img.load()

                nodata = self.nodataval
                def valuecountsgen():
                    allvals = (self._pixelaccess[x,y] for y in range(self.height) for x in range(self.width))
                    return (val for val in allvals if val != nodata)

                def _count():
                    return sum((1 for val in valuecountsgen))
                def _sum():
                    return sum((val for val in valuecountsgen))
                def _mean():
                    return _sum()/float(_count())
                def _min():
                    return min(valuecountsgen)
                def _max():
                    return max(valuecountsgen)
                
                if not stattypes or "count" in stattypes:
                    statsdict["count"] = _count()
                if not stattypes or "sum" in stattypes:
                    statsdict["sum"] = _sum()
                if not stattypes or "mean" in stattypes:
                    statsdict["mean"] = _mean()
                if not stattypes or "max" in stattypes:
                    statsdict["max"] = _max()
                if not stattypes or "min" in stattypes:
                    statsdict["min"] = _min()
                
        return statsdict

    def convert(self, mode):
        pilmode = rastmode_to_pilmode(mode)
        self.img = self.img.convert(pilmode)
        self._pixelaccess = None

    def copy(self):
        img = self.img.copy()
        band = Band(img=img, nodataval=self.nodataval)
        if self._cached_mask:
            band._cached_mask = self._cached_mask.copy()
        return band


class RasterData(object):
    def __init__(self, filepath=None, data=None, image=None,
                 mode=None, tilesize=None, tiles=None,
                 **kwargs):
        self.filepath = filepath

        # load
        if filepath:
            georef, nodataval, bands, crs = loader.from_file(filepath, **kwargs)
        elif data:
            georef, nodataval, bands, crs = loader.from_lists(data, **kwargs)
        elif image:
            georef, nodataval, bands, crs = loader.from_image(image, **kwargs)
        else:
            georef, nodataval, bands, crs = loader.new(**kwargs)

        # determine dimensions
        if any((filepath,data,image)):
            self.width, self.height = bands[0].size
            self.mode = pilmode_to_rastmode(bands[0].mode)

        else:
            # auto set width of new raster based on georef if needed
            if "width" not in kwargs:
                if "cellwidth" in kwargs:
                    kwargs["xscale"] = kwargs["cellwidth"]
                if "bbox" in kwargs and "xscale" in kwargs:
                    xwidth = kwargs["bbox"][2] - kwargs["bbox"][0]
                    kwargs["width"] = abs(int(round( xwidth / float(kwargs["xscale"]) )))
                    # adjust bbox based on rounded width
                    x1,y1,x2,y2 = kwargs["bbox"]
                    xwidth = kwargs["xscale"] * kwargs["width"]
                    kwargs["bbox"] = x1,y1,x1+xwidth,y2
                else:
                    raise Exception("Either the raster width or a bbox and xscale must be set")

            # auto set height of new raster based on georef if needed
            if "height" not in kwargs:
                if "cellheight" in kwargs:
                    kwargs["yscale"] = kwargs["cellheight"]
                if "bbox" in kwargs and "yscale" in kwargs:
                    yheight = kwargs["bbox"][3] - kwargs["bbox"][1]
                    kwargs["height"] = abs(int(round( yheight / float(kwargs["yscale"]) )))
                    # adjust bbox based on rounded width
                    x1,y1,x2,y2 = kwargs["bbox"]
                    yheight = kwargs["yscale"] * kwargs["height"]
                    kwargs["bbox"] = x1,y1,x2,y1+yheight
                else:
                    raise Exception("Either the raster height or a bbox and yscale must be set")

            # set the rest
            self.width = kwargs["width"]
            self.height = kwargs["height"]
            if mode:
                self.mode = mode
            else:
                raise Exception("A mode must be specified when creating a new empty raster from scratch")

        self.bands = [Band(img, nodataval=nodataval) for img in bands]
        self._cached_mask = None

        # set metadata
        self.crs = crs
        self.set_geotransform(**georef)

    def __len__(self):
        return len(self.bands)
    
    def __iter__(self):
        for band in self.bands:
            yield band

    def __repr__(self):
        import pprint
        return "RasterData object:\n" + pprint.pformat(self.meta, indent=4)

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
        new = RasterData(**self.meta)
        new.bands = [band.copy() for band in self.bands]
        new._cached_mask = self._cached_mask
        return new

    def add_band(self, band=None, **kwargs):
        """
        band is an existing Band() class, or use kwargs as init args for Band() class
        """
        if band:
            pass
        else:
            defaultargs = dict(mode=self.mode,
                               width=self.width,
                               height=self.height)
            defaultargs.update(kwargs)
            band = Band(**defaultargs)
            
        # check constraints
        if not band.width == self.width or not band.height == self.height:
            raise Exception("Added band must have the same dimensions as the raster dataset")

        elif band.mode != self.mode:
            raise Exception("Added band must have the same mode as the raster dataset")

        self.bands.append(band)

    def set_geotransform(self, **georef):
        
        # get coefficients needed to convert from raster to geographic space
        if "affine" in georef:
            # directly from affine coefficients
            [xscale, xskew, xoffset,
             yskew, yscale, yoffset] = georef["affine"]
        else:
            # more intuitive way
            [xscale, xskew, xoffset, yskew, yscale, yoffset] = loader.compute_affine(**georef)

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

    @property
    def mask(self):
        if self._cached_mask:
            return self._cached_mask

        else:
            if len(self) == 1:
                mask = self.bands[0].mask
            elif len(self) > 1:
                # mask out where all bands have nodata value
                # NOTE: wont work for floats, need another method...
                masks_namedict = dict([("mask%i"%i, band.mask) for i,band in enumerate(self.bands) ])
                expr = " & ".join(masks_namedict.keys())
                mask = PIL.ImageMath.eval(expr, **masks_namedict).convert("1")

            self._cached_mask = mask
            return self._cached_mask

    @mask.setter
    def mask(self, value):
        self._cached_mask = value

    def convert(self, mode):
        for band in self:
            band.convert(mode)
        self.mode = mode

    def save(self, filepath):
        saver.to_file(self.bands, self.meta, filepath)

    ##############################
    # Methods from other modules

    def resample(self, **kwargs):
        from . import manager
        kwargs["raster"] = self
        return manager.resample(**kwargs)

    def view(self, width, height, **options):
        from .. import renderer
        lyr = renderer.RasterLayer(self,
                                   **options
                                   )
        lyr.render(width=width, height=height, resampling="nearest")

        import Tkinter as tk
        import PIL.ImageTk
        
        app = tk.Tk()
        tkimg = PIL.ImageTk.PhotoImage(lyr.img)
        lbl = tk.Label(image=tkimg)
        lbl.tkimg = tkimg
        lbl.pack()
        app.mainloop()


def pilmode_to_rastmode(mode):
    rastmode = {"1":"1bit",
                
                "L":"int8",
                "P":"int8",
                
                "I:16":"int16",
                "I":"int32",
                
                "F:16":"float16",
                "F":"float32"}[mode]
    
    return rastmode

def rastmode_to_pilmode(mode):
    pilmode = {"1bit":"1",
                
                "int8":"L",
                "int8":"L",
                
                "int16":"I:16",
                "int32":"I",
                
                "float16":"F:16",
                "float32":"F"}[mode]
    
    return pilmode
