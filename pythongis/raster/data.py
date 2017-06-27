
# import builtins
import sys, os, itertools, operator

# import internals
from . import loader
from . import saver

# import PIL as the data container
import PIL.Image, PIL.ImageMath, PIL.ImageStat

# TODO:
# not sure if setting mask should paste nodatavals, or if only as a temporary overlay so that underlying values be kept (and only changed via compute etc)...
# also if conditional should query valid values only or all raw values...
# ie a strategy of convenience behind-the-scene handling or give direct raw handling of values and masks... 
# compute should only affect valid values, not nullvalues. 
# ...


class Cell(object):
    def __init__(self, band, col, row):
        self.band = band
        self.col, self.row = col, row
        self._x = None
        self._y = None

    def __repr__(self):
        return "Cell(col=%s, row=%s, value=%s)" %(self.col, self.row, self.value)

    def __geo_interface__(self):
        return self.poly
    
    @property
    def point(self):
        return {"type":"Point",
                "coordinates": (self.x, self.y)}

    @property
    def poly(self):
        trans = self.band._rast.cell_to_geo
        return {"type":"Polygon",
                "coordinates": [[trans(self.col-0.5, self.row-0.5),
                                 trans(self.col-0.5, self.row+0.5),
                                 trans(self.col+0.5, self.row+0.5),
                                 trans(self.col+0.5, self.row-0.5),
                                 ]]}

    @property
    def bbox(self):
        trans = self.band._rast.cell_to_geo
        corners = self.poly["coordinates"][0]
        xs,ys = zip(*corners)
        return min(xs),min(ys),max(xs),max(ys)

    @property
    def x(self):
        if None in (self._x,self._y):
            self._x, self._y = self.band._rast.cell_to_geo(self.col, self.row)
        return self._x

    @property
    def y(self):
        if None in (self._x,self._y):
            self._x, self._y = self.band._rast.cell_to_geo(self.col, self.row)
        return self._y

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

        if isinstance(img, basestring):
            img = PIL.Image.open(img)
        self.img = img

        self._pixelaccess = None
        self._cached_mask = None
        self._rast = None  # reference to owning raster, internal only

        self.nodataval = nodataval # calls on the setter method

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

    def _operator(self, other, op): 
        # calculate math
        # basic math + - * / ** %
        # note: logical ops ~ & | ^ makes binary mask and return the pixel value where mask is valid
        # note: relational ops < > == != return only binary mask
        # note: other useful is min() and max(), equiv to (r1 < r2) | r2
        if isinstance(other, (float,int)):
            if isinstance(other, int):
                md = "I"
            elif isinstance(other, float):
                md = "F"
            _oimg = PIL.Image.new(md, (self.width,self.height), other)
            other = Band(img=_oimg)
        
        bands = {"b1": self.img, "b2": other.img}
        if any((sym in op for sym in "&|^=><!")):
            img = PIL.ImageMath.eval("convert((b1 %s b2)*255, '1')" % op, **bands)
        else:
            img = PIL.ImageMath.eval("b1 %s b2" % op, **bands)

        # should maybe create a combined mask of nullvalues for all rasters
        # and filter away those nullcells from math result
        # ...
        masks = {"m1": self.mask, "m2": other.mask}
        mask = PIL.ImageMath.eval("convert(m1 | m2, '1')", **masks) # union of all masks

        # return result
        outband = Band(img=img)
        outband.mask = mask
        return outband

    

    def __add__(self, other):
        return self._operator(other, "+")

    def __sub__(self, other):
        return self._operator(other, "-")

    def __mul__(self, other):
        return self._operator(other, "*")

    def __div__(self, other):
        return self._operator(other, "/")

    def __truediv__(self, other):
        return self._operator(other, "/")

    def __pow__(self, other):
        return self._operator(other, "**")



    def __radd__(self, other):
        return other._operator(self, "+")

    def __rsub__(self, other):
        return other._operator(other, "-")

    def __rmul__(self, other):
        return other._operator(other, "*")

    def __rdiv__(self, other):
        return other._operator(self, "/")

    def __rtruediv__(self, other):
        return other._operator(self, "/")

    def __rpow__(self, other):
        return other._operator(self, "**")

    


    def __and__(self, other):
        return self._operator(other, "&")

    def __or__(self, other):
        return self._operator(other, "|")

    def __xor__(self, other):
        return self._operator(other, "^")



    def __lt__(self, other):
        return self._operator(other, "<")

    def __le__(self, other):
        return self._operator(other, "<=")

    def __eq__(self, other):
        return self._operator(other, "==")

    def __ne__(self, other):
        return self._operator(other, "!=")

    def __gt__(self, other):
        return self._operator(other, ">")

    def __ge__(self, other):
        return self._operator(other, ">=")
    


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
            
        # reset mask cache
        self._cached_mask = None

        # also reset the mask cache of the parent raster
        if self._rast:
            self._rast._cached_mask = None

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
    def mask(self, newmask):
        """Note, newmask must be PIL image and match band dimensions"""
        
        # paste nodatavals where mask is true
        self.img.paste(self.nodataval, mask=newmask)
        
        # cache it
        self._cached_mask = newmask

        # also reset the mask cache of the parent raster
        if self._rast:
            self._rast._cached_mask = None

    def compute(self, expr, condition=None):
        """Apply the given expression to recompute all values"""
        # get the mask before changing values
        mask = None
        if self.nodataval != None:
            mask = self.mask

        if condition:
            if isinstance(condition, basestring):
                condition = self.conditional(condition)
            condition = condition.img

        # change values
        self._compute(expr, condition)

        # use the original nodatamask to set null values again
        if mask:
            self.img.paste(self.nodataval, (0,0), mask)

    def _compute(self, expr, condition=None):
        """Internal only"""
        try:
            if "val" in expr:
                expr = "convert(%s, '%s')" % (expr, self.img.mode)
                result = PIL.ImageMath.eval(expr, val=self.img)
            else:
                val = eval(expr)
                result = PIL.Image.new(self.img.mode, self.img.size, val)
            if condition:
                self.img.paste(result, (0,0), condition)
            else:
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

            if condition:
                condpx = condition.load()
                for y in range(self.width):
                    for x in range(self.height):
                        if condpx[x,y]:
                            val = self._pixelaccess[x,y]
                            newval = eval(expr, {}, {"val":val})
                            self._pixelaccess[x,y] = forcetype(forcerange(newval))
            else:
                for y in range(self.width):
                    for x in range(self.height):
                        val = self._pixelaccess[x,y]
                        newval = eval(expr, {}, {"val":val})
                        self._pixelaccess[x,y] = forcetype(forcerange(newval))

    def recode(self, condition, newval):
        """Change to a new value for those pixels that meet a condition"""
        if isinstance(condition, basestring):
            condition = self._conditional(condition)
        if isinstance(newval, Band):
            newval = newval.img
        self.img.paste(newval, (0,0), condition)

    def conditional(self, condition):
        """Return a binary band showing where a condition is true"""
        
        result = self._conditional(condition)

        # set conditional to false for pixels covered by nodatamask
        #if self.nodataval != None:
        #    # TODO: should conditional really ignore nodatavals??? Prob not actually, should query actual raw values
        #    result.paste(0, (0,0), self.mask)

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
            if not stattypes or "median" in stattypes:
                sortedvals = list(sorted(self.img.getcolors(), key=lambda e: e[1]))
                statsdict["median"] = sortedvals[len(sortedvals)//2][1]
            if not stattypes or "majority" in stattypes:
                sortedvals = list(sorted(self.img.getcolors(), key=lambda e: e[0]))
                statsdict["majority"] = sortedvals[-1][1]
            if not stattypes or "minority" in stattypes:
                sortedvals = list(sorted(self.img.getcolors(), key=lambda e: e[0]))
                statsdict["minority"] = sortedvals[0][1]

        elif self.mode.endswith(("16","32","1bit")):
            
            try:
                # manually get count of all unique pixelvalues and do math on it
                # but do not include counts of nodataval
                
                nodata = self.nodataval
                valuecounts = [(cnt,val) for cnt,val in self.img.getcolors(self.width*self.height) if val != nodata]
                
                def _count():
                    return sum((cnt for cnt,val in valuecounts)) if valuecounts else 0
                def _sum():
                    return sum((cnt*val for cnt,val in valuecounts)) if valuecounts else None
                def _mean():
                    return _sum()/float(_count()) if valuecounts else None
                def _min():
                    return min((val for cnt,val in valuecounts)) if valuecounts else None
                def _max():
                    return max((val for cnt,val in valuecounts)) if valuecounts else None
                    
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
                if not stattypes or "median" in stattypes:
                    sortedvals = list(sorted(valuecounts, key=lambda e: e[1]))
                    statsdict["median"] = sortedvals[len(sortedvals)//2][1] if sortedvals else None
                if not stattypes or "majority" in stattypes:
                    sortedvals = list(sorted(valuecounts, key=lambda e: e[0]))
                    statsdict["majority"] = sortedvals[-1][1] if sortedvals else None
                if not stattypes or "minority" in stattypes:
                    sortedvals = list(sorted(valuecounts, key=lambda e: e[0]))
                    statsdict["minority"] = sortedvals[0][1] if sortedvals else None
                
            except MemoryError:

                # getcolors() resulted in too many values at once
                # so fallback on manual iteration one pixel at a time

                if not self._pixelaccess:
                    self._pixelaccess = self.img.load()

                nodata = self.nodataval
                allvals = (self._pixelaccess[x,y] for y in range(self.height) for x in range(self.width))
                values = [val for val in allvals if val != nodata]

                def _count():
                    return sum((1 for val in values)) if values else 0
                def _sum():
                    return sum((val for val in values)) if values else None
                def _mean():
                    return _sum()/float(_count()) if values else None
                def _min():
                    return min(values) if values else None
                def _max():
                    return max(values) if values else None
                
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
                # some more stats
                if not stattypes or "median" in stattypes:
                    sortedvals = list(sorted(values))
                    statsdict["median"] = sortedvals[len(sortedvals)//2] if sortedvals else None
                if not stattypes or "majority" in stattypes:
                    sortedvals = list(sorted(values))
                    statsdict["majority"] = sortedvals[-1] if sortedvals else None
                if not stattypes or "minority" in stattypes:
                    sortedvals = list(sorted(values))
                    statsdict["minority"] = sortedvals[0] if sortedvals else None
                
        return statsdict

    def clear(self):
        # not fully tested yet...
        na = self.nodataval
        if na is None: na = 0
        self.img.paste(na)

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

##    def render(self, width, height, **options):
##        if self._rast:
##            rast = self._rast
##            options.update(bandnum=rast.bands.index(self))
##        else:
##            rast = RasterData(mode=self.mode, width=width, height=height, xoffset=0, yoffset=0, xscale=1, yscale=1)
##            rast.add_band()
##        return rast.render(width, height, **options)
##
##    def view(self, width, height, **options):
##        lyr = self.render(width, height, **options)
##
##        import Tkinter as tk
##        import PIL.ImageTk
##        
##        app = tk.Tk()
##        tkimg = PIL.ImageTk.PhotoImage(lyr.img)
##        lbl = tk.Label(image=tkimg)
##        lbl.tkimg = tkimg
##        lbl.pack()
##        app.mainloop()

    def histogram(self, width=None, height=None, bins=10):
        import pyagg
        stats = self.summarystats("min","max")
        binsize = (stats["max"] - stats["min"]) / float(bins)
        bars = []
        cur = stats["min"]
        while cur < stats["max"]:
            below = self.conditional("%s < val" % cur)
            above = self.conditional("val < %s" % (cur+binsize))
            maskimg = PIL.ImageMath.eval("b & a", b=below.img, a=above.img)
            #maskimg.show()
            mask = Band(img=maskimg)
            label = "%s to %s" % (cur, cur+binsize)
            count = mask.summarystats("sum")["sum"]
            bars.append((label,count))
            cur += binsize
        c = pyagg.graph.BarChart()
        c.add_category(name="Title...", baritems=bars)
        return c.draw() # draw returns the canvas

    def render(self, width=None, height=None, bbox=None, title="", background=None, **styleoptions):
        # WARNING: CANNOT USE TO GET A MAP AND THEN ADDING OTHER LAYERS,
        # GETS ALL MISMATCHED AND JUMPS AROUND
        from .. import renderer
        
        rast = self._rast
        if rast:
            styleoptions.update(bandnum=rast.bands.index(self))
        else:
            #raise Exception("Cannot render a freestanding band without a parent raster which is needed for georeferencing")
            rast = RasterData(mode=pilmode_to_rastmode(self.img.mode),
                              bbox=[0,0,self.width,self.height], width=self.width, height=self.height)
            rast.add_band(self)
            styleoptions.update(bandnum=0)
        
        mapp = renderer.Map(width, height, title=title, background=background)
        mapp.add_layer(rast, **styleoptions)
        if bbox:
            mapp.zoom_bbox(*bbox)
        else:
            mapp.zoom_bbox(*mapp.layers.bbox)
        mapp.render_all()
        return mapp

    def view(self, width=None, height=None, bbox=None, title="", background=None, **styleoptions):
        from .. import app
        mapp = self.render(width, height, bbox, title=title, background=background, **styleoptions)
        # make gui
        win = app.builder.MultiLayerGUI(mapp)
        win.mainloop()

    def save(self, filepath):
        self.img.save(filepath)



def Name_generator():
    i = 1
    while True:
        yield "Untitled%s" % i
        i += 1


NAMEGEN = Name_generator()



class RasterData(object):
    def __init__(self, filepath=None, data=None, name=None,
                 image=None,
                 mode=None, tilesize=None, tiles=None,
                 **kwargs):
        self.filepath = filepath
        self.name = name or filepath
        if not self.name:
            self.name = next(NAMEGEN)

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
            if "width" not in georef:
                if "cellwidth" in georef:
                    georef["xscale"] = georef["cellwidth"]
                if "bbox" in georef and "xscale" in georef:
                    xwidth = georef["bbox"][2] - georef["bbox"][0]
                    georef["width"] = abs(int(round( xwidth / float(georef["xscale"]) )))
                    # adjust bbox based on rounded width
                    x1,y1,x2,y2 = georef["bbox"]
                    xwidth = georef["xscale"] * georef["width"]
                    georef["bbox"] = x1,y1,x1+xwidth,y2
                else:
                    raise Exception("Either the raster width or a bbox and xscale must be set")

            # auto set height of new raster based on georef if needed
            if "height" not in georef:
                if "cellheight" in georef:
                    georef["yscale"] = georef["cellheight"]
                if "bbox" in georef and "yscale" in georef:
                    yheight = georef["bbox"][3] - georef["bbox"][1]
                    georef["height"] = abs(int(round( yheight / float(georef["yscale"]) )))
                    # adjust bbox based on rounded width
                    x1,y1,x2,y2 = georef["bbox"]
                    yheight = georef["yscale"] * georef["height"]
                    georef["bbox"] = x1,y1,x2,y1+yheight
                else:
                    raise Exception("Either the raster height or a bbox and yscale must be set")

            # set the rest
            self.width = georef["width"]
            self.height = georef["height"]
            if mode:
                self.mode = mode
            else:
                raise Exception("A mode must be specified when creating a new empty raster from scratch")

        self.bands = [Band(img, nodataval=nodataval) for img in bands]
        self._cached_mask = None

        # store reference to raster to enable pixel convenience methods
        for b in self.bands:
            b._rast = self

        # set metadata
        self.crs = crs
        self.set_geotransform(**georef)

    def __len__(self):
        return len(self.bands)
    
    def __iter__(self):
        for band in self.bands:
            yield band

    def __repr__(self):
        return "<Raster data: mode={mode} bands={bands} size={size} bbox={bbox}>".format(mode=self.mode,
                                                                                         bands=len(self),
                                                                                         size=(self.width,self.height),
                                                                                         bbox=self.bbox)

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
                        affine=self.affine,
                        bbox=self.bbox)
        return metadict

    @property
    def rasterdef(self):
        metadict = dict(width=self.width,
                        height=self.height,
                        affine=self.affine)
        return metadict

    @property
    def bbox(self):
        # get corner coordinates of raster (including cell area corners, not just centroids)
        xleft_coord,ytop_coord = self.cell_to_geo(0-0.5, 0-0.5)
        xright_coord,ybottom_coord = self.cell_to_geo(self.width-1+0.5, self.height-1+0.5)
        return [xleft_coord,ytop_coord,xright_coord,ybottom_coord]

    def copy(self, shallow=False):
        new = RasterData(**self.meta)
        if shallow:
            new.bands = []
        else:
            new.bands = [band.copy() for band in self.bands]
        new._cached_mask = self._cached_mask
        return new

    def get(self, x, y, band):
        if not isinstance(band, Band):
            band = self.bands[band]

        col,row = self.geo_to_cell(x, y)
        return band.get(col,row)

    def set(self, x, y, value, band):
        if not isinstance(band, Band):
            band = self.bands[band]

        col,row = self.geo_to_cell(x, y)
        band.set(col,row,value)

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

        # store reference to raster to enable pixel convenience methods
        band._rast = self

        self.bands.append(band)

        return band

    def set_geotransform(self, **georef):
        
        # get coefficients needed to convert from raster to geographic space
        if "affine" in georef:
            # directly from affine coefficients
            [xscale, xskew, xoffset,
             yskew, yscale, yoffset] = georef["affine"]
        else:
            # more intuitive way
            current = dict(zip("xscale xskew xoffset yskew yscale yoffset".split(), self.meta["affine"]))
            current.update(georef)
            georef = current
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
                # mask out where all band masks are true
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

    def render(self, width=None, height=None, bbox=None, title="", background=None, **styleoptions):
        from .. import renderer
        mapp = renderer.Map(width, height, title=title, background=background)
        mapp.add_layer(self, **styleoptions)
        if bbox:
            mapp.zoom_bbox(*bbox)
        else:
            mapp.zoom_bbox(*mapp.layers.bbox)
        mapp.render_all()
        return mapp

    def view(self, width=None, height=None, bbox=None, title="", background=None, **styleoptions):
        from .. import app
        mapp = self.render(width, height, bbox, title=title, background=background, **styleoptions)
        # make gui
        win = app.builder.MultiLayerGUI(mapp)
        win.mainloop()


def pilmode_to_rastmode(mode):
    rastmode = {"1":"1bit",
                
                "L":"int8",
                "P":"int8",
                
                "I;16":"int16",
                "I":"int32",
                
                "F;16":"float16",
                "F":"float32"}[mode]
    
    return rastmode

def rastmode_to_pilmode(mode):
    pilmode = {"1bit":"1",
                
                "int8":"L",
                "int8":"L",
                
                "int16":"I;16",
                "int32":"I",
                
                "float16":"F;16",
                "float32":"F"}[mode]
    
    return pilmode
