
import random
import itertools
import pyagg, pyagg.legend
import PIL, PIL.Image

from .vector.data import VectorData
from .raster.data import RasterData

from .exceptions import UnknownFileError

class Map:
    def __init__(self, width, height, background=None, layers=None, title="", titleoptions=None, *args, **kwargs):

        # remember and be remembered by the layergroup
        if not layers:
            layers = LayerGroup()
        self.layers = layers
        layers.connected_maps.append(self)

        # create the drawer with a default unprojected lat-long coordinate system
        self.drawer = pyagg.Canvas(width, height, background)
        self.drawer.geographic_space() 

        # foreground layergroup for non-map decorations
        self.foreground = ForegroundLayerGroup()

        # title (would be good to make these properties affect the actual rendered title after init)
        self.title = title
        self.titleoptions = titleoptions
        if title:
            titleoptions = titleoptions or dict()
            self.add_title(title, **titleoptions)

        self.dimensions = dict()
            
        self.img = self.drawer.get_image()

    def copy(self):
        dupl = Map(self.drawer.width, self.drawer.height, layers=self.layers.copy(), title=self.title, titleoptions=self.titleoptions)
        dupl.drawer = self.drawer.copy()
        dupl.foreground = self.foreground.copy()
        return dupl

    def pixel2coord(self, x, y):
        return self.drawer.pixel2coord(x, y)

    # Map canvas alterations

    def offset(self, xmove, ymove):
        self.drawer.move(xmove, ymove)

    def resize(self, width, height):
        self.drawer.resize(width, height, lock_ratio=True)
        self.img = self.drawer.get_image()

    # Zooming

    def zoom_bbox(self, xmin, ymin, xmax, ymax):
        self.drawer.zoom_bbox(xmin, ymin, xmax, ymax)

    def zoom_in(self, factor, center=None):
        self.drawer.zoom_in(factor, center=center)

    def zoom_out(self, factor, center=None):
        self.drawer.zoom_out(factor, center=center)

    def zoom_units(self, units, center=None):
        self.drawer.zoom_units(units, center=center)

    # Layers

    def __iter__(self):
        for layer in self.layers:
            yield layer

    def add_layer(self, layer, **options):
        return self.layers.add_layer(layer, **options)

    def move_layer(self, from_pos, to_pos):
        self.layers.move_layer(from_pos, to_pos)

    def remove_layer(self, position):
        self.layers.remove_layer(position)

    def get_position(self, layer):
        return self.layers.get_position(layer)

    # Legend

    def add_legend(self, legend=None, legendoptions=None, **pasteoptions):
        if not legend:
            # auto creates and builds legend
            legendoptions = legendoptions or dict()
            legend = Legend(self, **legendoptions)
            legend.autobuild()
            
        legend.pasteoptions = pasteoptions
        self.foreground.add_layer(legend)
        return legend

    # Decorations

    def add_title(self, title, titleoptions=None, **pasteoptions):
        # a little hacky, since uses pyagg label object directly,
        # better if canvas could allow percent coord units
        # ...
        override = titleoptions or dict()
        titleoptions = dict(textsize=18)
        titleoptions.update(override)
        decor = pyagg.legend.Label(title, **titleoptions) # pyagg label indeed implements a render method()
        defaultpaste = dict(xy=("50%w","1%h"), anchor="n")
        defaultpaste.update(pasteoptions)
        decor.pasteoptions = defaultpaste
        decor.img = decor.render()
        print self.foreground,self.foreground._layers
        self.foreground.add_layer(decor)
        
    def add_decoration(self, funcname, *args, **kwargs):
        # draws directly on an image the size of the map canvas, so no pasteoptions needed
        decor = Decoration(self, funcname, *args, **kwargs)
        decor.pasteoptions = dict() #xy=(0,0), anchor="nw")
        self.foreground.add_layer(decor)

##    def draw_grid(self, xinterval, yinterval, **kwargs):
##        self.drawer.draw_grid(xinterval, yinterval, **kwargs)
##
##    def draw_axis(self, axis, minval, maxval, intercept,
##                  tickpos=None,
##                  tickinterval=None, ticknum=5,
##                  ticktype="tick", tickoptions={},
##                  ticklabelformat=None, ticklabeloptions={},
##                  noticks=False, noticklabels=False,
##                  **kwargs):
##        self.drawer.draw_axis(axis, minval, maxval, intercept,
##                              tickpos=tickpos, tickinterval=tickinterval, ticknum=ticknum,
##                              ticktype=ticktype, tickoptions=tickoptions,
##                              ticklabelformat=ticklabelformat, ticklabeloptions=ticklabeloptions,
##                              noticks=noticks, noticklabels=noticklabels,
##                              **kwargs)

    # Batch utilities

    def add_dimension(self, dimtag, dimvalues):
        self.dimensions[dimtag] = dimvalues # list of dimval-dimfunc pairs

    def iter_dimensions(self, groupings=None):
        # collect all dimensions from layers and the map itself as a flat list
        alldimensions = dict()
##        for lyr in self:
##            if lyr.dimensions: 
##                alldimensions.update(lyr.dimensions) # note, duplicate dim names will be overwritten
        alldimensions.update(self.dimensions)
        
        # yield all dimensions as all possible value combinations of each other
        dimtagvalpairs = [[(dimtag,dimval) for dimval,dimfunc in dimvalues] for dimtag,dimvalues in alldimensions.items()]
        allcombis = itertools.product(*dimtagvalpairs)

        def submapgen():
            for dimcombi in allcombis:
                # create the map and run all the functions for that combination
                submap = self.copy()
                for dimtag,dimval in dimcombi:
                    dimfunc = next((_dimfunc for _dimval,_dimfunc in alldimensions[dimtag] if dimval == _dimval),None)  # first instance where dimval matches, same as dict lookup inside a list of keyval pairs
                    dimfunc(submap)
                dimdict = dict(dimcombi)
                yield dimdict,submap
                
        if groupings:
            # yield all grouped by each unique value combination belonging to the dimension names specified in groupings
            # eg grouping by a region dimension will return groups of dimdict,submap for each unique value of region

            def key(item):
                dimdict,submap = item
                keyval = [dimdict[gr] for gr in groupings]
                return keyval
            
            for _id,dimcombis in itertools.groupby(sorted(submapgen(),key=key), key=key):
                yield list(dimcombis) # list of dimdict,submap pairs belonging to same group

        else:
            # yield all flat, one by one
            for dimdict,submap in submapgen():
                yield dimdict,submap

    # Drawing

    def render_one(self, layer):
        if layer.visible:
            layer.render(width=self.drawer.width,
                         height=self.drawer.height,
                         coordspace_bbox=self.drawer.coordspace_bbox)
            self.update_draworder()

    def render_all(self):
        for layer in self.layers:
            if layer.visible:
                layer.render(width=self.drawer.width,
                             height=self.drawer.height,
                             bbox=self.drawer.coordspace_bbox)
        for layer in self.foreground:
            layer.render()
        self.update_draworder()

    def update_draworder(self):
        self.drawer.clear()

        # paste the map layers
        for layer in self.layers:
            if layer.visible:
                self.drawer.paste(layer.img)

        # paste the foreground decorations
        for layer in self.foreground:
            if layer.img:
                self.drawer.paste(layer.img, **layer.pasteoptions)
                
        self.img = self.drawer.get_image()

    def get_tkimage(self):
        # Special image format needed by Tkinter to display it in the GUI
        return self.drawer.get_tkimage()

    def view(self):
        self.drawer.view()

    def save(self, savepath):
        self.drawer.save(savepath)

        


class LayerGroup:
    def __init__(self):
        self._layers = list()
        self.connected_maps = list()
        self.dimensions = dict()

    def __iter__(self):
        for layer in self._layers:
            yield layer

    def add_dimension(self, dimtag, dimvalues):
        # used by parent map to batch render all varieties of this layer
        self.dimensions[dimtag] = dimvalues # list of dimval-dimfunc pairs

    def copy(self):
        layergroup = LayerGroup()
        layergroup._layers = list(self._layers)
        return layergroup

    def add_layer(self, layer, **options):
        if not isinstance(layer, (VectorLayer,RasterLayer)):
            try:
                layer = VectorLayer(layer, **options)
            except UnknownFileError:
                layer = RasterLayer(layer, **options)
        self._layers.append(layer)

        return layer

    def move_layer(self, from_pos, to_pos):
        layer = self._layers.pop(from_pos)
        self._layers.insert(to_pos, layer)

    def remove_layer(self, position):
        self._layers.pop(position)

    def get_position(self, layer):
        return self._layers.index(layer)




class ForegroundLayerGroup(LayerGroup):
    def add_layer(self, layer, **options):
        self._layers.append(layer, **options)

    def copy(self):
        foreground = ForegroundLayerGroup()
        foreground._layers = list(self._layers)
        return foreground




class VectorLayer:
    def __init__(self, data, legendoptions=None, nolegend=False, datafilter=None, **options):

        if not isinstance(data, VectorData):
            # assume data is filepath
            dtoptions = options.get("dataoptions", dict())
            data = VectorData(data, **dtoptions)
        
        self.data = data
        self.visible = True
        self.img = None

        self.legendoptions = legendoptions or dict()
        self.nolegend = nolegend
        self.datafilter = datafilter
        
        # by default, set random style color
        rand = random.randrange
        randomcolor = (rand(255), rand(255), rand(255), 255)
        self.styleoptions = {"fillcolor": randomcolor,
                             "sortorder": "incr"}
            
        # override default if any manually specified styleoptions
        self.styleoptions.update(options)

        # set up classifier
        features = list(self.data) # classifications should be based on all features and not be affected by datafilter, thus enabling keeping the same classification across subsamples
        import classipy as cp
        for key,val in self.styleoptions.copy().items():
            if key in "fillcolor fillsize outlinecolor outlinewidth".split():
                if isinstance(val, dict):
                    # cache precalculated values in id dict
                    # more memory friendly alternative is to only calculate breakpoints
                    # and then find classvalue for feature when rendering,
                    # which is likely slower
                    if val["breaks"] == "unique" and "valuestops" not in val:
                        rand = random.randrange
                        val["valuestops"] = [(rand(255), rand(255), rand(255))
                                             for _ in range(20)] 
                    classifier = cp.Classifier(features, **val)
                    self.styleoptions[key] = dict(classifier=classifier,
                                                   symbols=dict((id(f),classval) for f,classval in classifier)
                                                   )
                else:
                    self.styleoptions[key] = val

    def features(self, bbox=None):
        # get features based on spatial index, for better speeds when zooming
        if bbox:
            if not hasattr(self.data, "spindex"):
                self.data.create_spatial_index()
            features = self.data.quick_overlap(bbox)
        else:
            features = self.data
        
        if self.datafilter:
            for feat in features:
                if self.datafilter(feat):
                    yield feat
        else:
            for feat in features:
                yield feat

    def render(self, width, height, bbox=None, lock_ratio=True, flipy=False):
        if not bbox:
            bbox = self.data.bbox

        if flipy:
            bbox = bbox[0],bbox[3],bbox[2],bbox[1]
        
        drawer = pyagg.Canvas(width, height, background=None)
        drawer.custom_space(*bbox, lock_ratio=lock_ratio)

        
        features = self.features(bbox=bbox)

        # custom draworder (sortorder is only used with sortkey)
        if "sortkey" in self.styleoptions:
            features = sorted(features, key=self.styleoptions["sortkey"],
                              reverse=self.styleoptions["sortorder"].lower() == "decr")

        # draw each as geojson
        for feat in features:
            
            # get symbols
            rendict = dict()
            for key in "fillcolor fillsize outlinecolor outlinewidth".split():
                nullval = None if "color" in key else 0 # this means symbol defaults to None ie transparent for colors and 0 for sizes if feature had a missing/null value, which should be correct
                if key in self.styleoptions:
                    val = self.styleoptions[key]
                    if isinstance(val, dict):
                        # lookup self in precomputed symboldict
                        rendict[key] = val["symbols"].get(id(feat),nullval) 
                    else:
                        rendict[key] = val

            # draw
            drawer.draw_geojson(feat.geometry, **rendict)
            
        self.img = drawer.get_image()



        
class RasterLayer:
    def __init__(self, data, legendoptions=None, nolegend=False, **options):
        
        if not isinstance(data, RasterData):
            # assume data is filepath
            doptions = options.get("dataoptions", dict())
            data = RasterData(data, **doptions)
        
        self.data = data
        self.visible = True
        self.img = None

        self.legendoptions = legendoptions or dict()
        self.nolegend = nolegend

        # by default, set random style color
        if not "type" in options:
            if len(data.bands) == 3:
                options["type"] = "rgb"
            else:
                options["type"] = "colorscale"

        if options["type"] == "grayscale":
            options["bandnum"] = options.get("bandnum", 0)
            band = self.data.bands[options["bandnum"]]
            
            # retrieve min and maxvals from data if not manually specified
            if not "minval" in options:
                options["minval"] = band.summarystats("min")["min"]
            if not "maxval" in options:
                options["maxval"] = band.summarystats("max")["max"]

        elif options["type"] == "colorscale":
            options["bandnum"] = options.get("bandnum", 0)
            band = self.data.bands[options["bandnum"]]
            
            # retrieve min and maxvals from data if not manually specified
            if not "minval" in options:
                options["minval"] = band.summarystats("min")["min"]
            if not "maxval" in options:
                options["maxval"] = band.summarystats("max")["max"]

            # set random gradient
            if not "gradcolors" in options:
                rand = random.randrange
                randomcolor = (rand(255), rand(255), rand(255), 255)
                randomcolor2 = (rand(255), rand(255), rand(255), 255)
                options["gradcolors"] = [randomcolor,randomcolor2]

        elif options["type"] == "rgb":
            options["r"] = options.get("r", 0)
            options["g"] = options.get("g", 1)
            options["b"] = options.get("b", 2)
            
        # remember style settings
        self.styleoptions = options

    def render(self, resampling="nearest", lock_ratio=True, **georef):
        # position in space
        # TODO: USING BBOX HERE RESULTS IN SLIGHT OFFSET, SOMEHOW NOT CORRECT FOR RESAMPLE
        # LIKELY DUE TO HALF CELL CENTER VS CORNER
        if "bbox" not in georef:
            georef["bbox"] = self.data.bbox

        rendered = self.data.resample(algorithm=resampling, **georef)

        # TODO: Instead of resample need to somehow honor lock_ratio, maybe by not using from_image()
        # ...

        # TODO: binary 1bit rasters dont show correctly
        # ...

        if self.styleoptions["type"] == "grayscale":
            
            # Note: Maybe remove and instead must specify white and black in colorscale type...?
            # ...
            
            band = rendered.bands[self.styleoptions["bandnum"]]
            
            # equalize
            minval,maxval = self.styleoptions["minval"], self.styleoptions["maxval"]
            valrange = 1/float(maxval-minval) * 255 if maxval-minval != 0 else 0
            expr = "(val - {minval}) * {valrange}".format(minval=minval,valrange=valrange)
            band.compute(expr)
            # colorize
            img = band.img.convert("LA")

        elif self.styleoptions["type"] == "colorscale":
            band = rendered.bands[self.styleoptions["bandnum"]]
            
            # equalize
            minval,maxval = self.styleoptions["minval"], self.styleoptions["maxval"]
            valrange = 1/float(maxval-minval) * 255 if maxval-minval != 0 else 0
            expr = "(val - {minval}) * {valrange}".format(minval=minval,valrange=valrange)
            band.compute(expr)
            # colorize
            canv = pyagg.canvas.from_image(band.img.convert("RGBA"))
            canv = canv.color_remap(self.styleoptions["gradcolors"])
            img = canv.get_image()

        elif self.styleoptions["type"] == "rgb":
            rband = rendered.bands[self.styleoptions["r"]].img.convert("L")
            gband = rendered.bands[self.styleoptions["g"]].img.convert("L")
            bband = rendered.bands[self.styleoptions["b"]].img.convert("L")
            img = PIL.Image.merge("RGB", [rband,gband,bband])
            img = img.convert("RGBA")

        elif self.styleoptions["type"] == "3d surface":
            import matplotlib as mpl
            # ...
            pass

        # make edge and nodata mask transparent
        
        #blank = PIL.Image.new("RGBA", img.size, None)
        #blank.paste(img, mask=rendered.mask)
        #img = blank
        #r,g,b = img.split()[:3]
        #a = rendered.mask.convert("L")
        #rgba = (r,g,b,a)
        #img = PIL.Image.merge("RGBA", rgba)
        #img.putalpha(rendered.mask)
        #img.show()
        #rendered.mask.show()

        img.paste(0, mask=rendered.mask) # sets all bands to 0 incl the alpha band

        # final
        self.img = img


class Legend:
    def __init__(self, map, **options):
        self.map = map
        self.img = None
        self._legend = pyagg.legend.Legend(refcanvas=map.drawer, **options)

    def add_fillcolors(self, layer, **override):
        if isinstance(layer, VectorLayer):
            if "Polygon" in layer.data.type:
                shape = "polygon"
            elif "Line" in layer.data.type:
                shape = "line"
            elif "Point" in layer.data.type:
                shape = "circle"
            else:
                raise Exception("Legend layer data must be of type polygon, linestring, or point")

            # use layer's legendoptions and possibly override
            options = dict(layer.legendoptions)
            options.update(override)

            if "fillcolor" in layer.styleoptions and isinstance(layer.styleoptions["fillcolor"], dict):
                cls = layer.styleoptions["fillcolor"]["classifier"]

                # force to categorical if classifier algorithm is unique
                if cls.algo == "unique": options["valuetype"] = "categorical"

                # detect valuetype
                if options.get("valuetype") == "categorical":
                    # WARNING: not very stable yet...
                    categories = set((cls.key(item),tuple(classval)) for item,classval in cls) # only the unique keys
                    breaks,classvalues = zip(*sorted(categories, key=lambda e:e[0]))
                else:
                    breaks = cls.breaks
                    classvalues = cls.classvalues

                # add any other nonvarying layer options
                for k in "fillsize outlinecolor outlinewidth".split():
                    if k not in options and k in layer.styleoptions:
                        v = layer.styleoptions[k]
                        if not isinstance(v, dict):
                            options[k] = v

                print options
                
                self._legend.add_fillcolors(shape, breaks, classvalues, **options)

            else:
                # add as static symbol if none of the dynamic ones
                # self.add_single_symbol()
                raise Exception("Not yet implemented")

        elif isinstance(layer, RasterLayer):
            shape = "polygon"
            # ...
            raise Exception("Legend layer for raster data not yet implemented")

    def add_fillsizes(self, layer, **override):
        if isinstance(layer, VectorLayer):
            if "Polygon" in layer.data.type:
                shape = "polygon"
            elif "Line" in layer.data.type:
                shape = "line"
            elif "Point" in layer.data.type:
                shape = "circle"
            else:
                raise Exception("Legend layer data must be of type polygon, linestring, or point")

            # use layer's legendoptions and possibly override
            options = dict(layer.legendoptions)
            options.update(override)
            
            if "fillsize" in layer.styleoptions and isinstance(layer.styleoptions["fillsize"], dict):
                
                # add any other nonvarying layer options
                print 9999
                print options
                for k in "fillcolor outlinecolor outlinewidth".split():
                    print k
                    if k not in options and k in layer.styleoptions:
                        v = layer.styleoptions[k]
                        print k,v,type(v)
                        if not isinstance(v, dict):
                            options[k] = v
                            
                print options

                cls = layer.styleoptions["fillsize"]["classifier"]
                self._legend.add_fillsizes(shape, cls.breaks, cls.classvalues, **options)

            else:
                # add as static symbol if none of the dynamic ones
                # self.add_single_symbol()
                raise Exception("Not yet implemented")

        elif isinstance(layer, RasterLayer):
            raise Exception("Fillcolor is the only possible legend entry for a raster layer")

    def autobuild(self):
        # build the legend automatically
        for layer in self.map:
            if not layer.nolegend:
                # Todo: better handling when more than one classipy option for same layer
                # perhaps grouping into basegroup under same layer label
                # ...
                anydynamic = False
                if "fillcolor" in layer.styleoptions and isinstance(layer.styleoptions["fillcolor"], dict):
                    # is dynamic and should be highlighted specially
                    print 999,layer,layer.legendoptions
                    self.add_fillcolors(layer, **layer.legendoptions)
                    anydynamic = True
                if "fillsize" in layer.styleoptions and isinstance(layer.styleoptions["fillsize"], dict):
                    # is dynamic and should be highlighted specially
                    self.add_fillsizes(layer, **layer.legendoptions)
                    anydynamic = True
                    
                # add as static symbol if none of the dynamic ones
                if not anydynamic:
                    # self.add_single_symbol()
                    raise Exception("Not yet implemented")

    def render(self):
        # render it
        rendered = self._legend.render()
        self.img = rendered.get_image()




class Decoration:
    def __init__(self, map, funcname, *args, **kwargs):
        self.map = map
        
        self.funcname = funcname
        self.args = args
        self.kwargs = kwargs

        self.img = None
        
    def render(self):
        drawer = pyagg.Canvas(self.map.drawer.width, self.map.drawer.height, background=None)
        drawer.custom_space(*self.map.drawer.coordspace_bbox)
        func = getattr(drawer,self.funcname)
        func(*self.args, **self.kwargs)
        self.img = drawer.get_image()
        

        
