
import random
import pyagg, pyagg.legend
import PIL, PIL.Image

from .vector.data import VectorData
from .raster.data import RasterData

class Map:
    def __init__(self, width, height, background=None, layers=None, *args, **kwargs):

        # remember and be remembered by the layergroup
        if not layers:
            layers = LayerGroup()
        self.layers = layers
        layers.connected_maps.append(self)

        # create the drawer with a default unprojected lat-long coordinate system
        self.drawer = pyagg.Canvas(width, height, background)
        self.drawer.geographic_space() 

        self.img = self.drawer.get_image()

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

    def draw_legend(self, legend, **options):
        self.drawer.paste(legend._legend.render(), **options)

    # Decorations

    def draw_grid(self, xinterval, yinterval, **kwargs):
        self.drawer.draw_grid(xinterval, yinterval, **kwargs)

    def draw_axis(self, axis, minval, maxval, intercept,
                  tickpos=None,
                  tickinterval=None, ticknum=5,
                  ticktype="tick", tickoptions={},
                  ticklabelformat=None, ticklabeloptions={},
                  noticks=False, noticklabels=False,
                  **kwargs):
        self.drawer.draw_axis(axis, minval, maxval, intercept,
                              tickpos=tickpos, tickinterval=tickinterval, ticknum=ticknum,
                              ticktype=ticktype, tickoptions=tickoptions,
                              ticklabelformat=ticklabelformat, ticklabeloptions=ticklabeloptions,
                              noticks=noticks, noticklabels=noticklabels,
                              **kwargs)

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
        self.update_draworder()

    def update_draworder(self):
        self.drawer.clear()
        for layer in self.layers:
            if layer.visible:
                self.drawer.paste(layer.img)
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

    def __iter__(self):
        for layer in self._layers:
            yield layer

    def add_layer(self, layer, **options):
        if not isinstance(layer, (VectorLayer,RasterLayer)):
            try:
                layer = VectorLayer(layer, **options)
            except:
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




class VectorLayer:
    def __init__(self, data, name=None, **options):

        if not isinstance(data, VectorData):
            # assume data is filepath
            doptions = options.get("dataoptions", dict())
            data = VectorData(data, **doptions)
        
        self.data = data
        self.visible = True
        self.img = None

        self.name = name
        
        # by default, set random style color
        rand = random.randrange
        randomcolor = (rand(255), rand(255), rand(255), 255)
        self.styleoptions = {"fillcolor": randomcolor,
                             "sortorder": "incr"}
            
        # override default if any manually specified styleoptions
        self.styleoptions.update(options)

        # set up classifier
        features = self.data
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

    def render(self, width, height, bbox=None, lock_ratio=True, flipy=False):
        if not bbox:
            bbox = self.data.bbox

        if flipy:
            bbox = bbox[0],bbox[3],bbox[2],bbox[1]
        
        drawer = pyagg.Canvas(width, height, background=None)
        drawer.custom_space(*bbox, lock_ratio=lock_ratio)

        # get features based on spatial index, for better speeds when zooming
        if not hasattr(self.data, "spindex"):
            self.data.create_spatial_index()
        features = self.data.quick_overlap(bbox)

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
    def __init__(self, data, name=None, **options):
        
        if not isinstance(data, RasterData):
            # assume data is filepath
            doptions = options.get("dataoptions", dict())
            data = RasterData(data, **doptions)
        
        self.data = data
        self.visible = True
        self.img = None

        self.name = name

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
        self._legend = pyagg.legend.Legend(refcanvas=map.drawer, **options)

    def add_fillcolors(self, layer, **options):
        if isinstance(layer, VectorLayer):
            if "Polygon" in layer.data.type:
                shape = "polygon"
            elif "Line" in layer.data.type:
                shape = "line"
            elif "Point" in layer.data.type:
                shape = "circle"
            else:
                raise Exception("Legend layer data must be of type polygon, linestring, or point")

            cls = layer.styleoptions["fillcolor"]["classifier"]
            if options.get("valuetype") == "categorical":
                # WARNING: not very stable yet...
                categories = set((cls.key(item),tuple(classval)) for item,classval in cls) # only the unique keys
                breaks,classvalues = zip(*sorted(categories, key=lambda e:e[0]))
            else:
                breaks = cls.breaks
                classvalues = cls.classvalues

            # add title automatically
            if not "title" in options and layer.name:
                options["title"] = layer.name

            # add any other nonvarying layer options
            options = dict(options)
            for k in "fillsize outlinecolor outlinewidth".split():
                if k not in options and k in layer.styleoptions:
                    v = layer.styleoptions[k]
                    if not isinstance(v, dict):
                        options[k] = v
            
            self._legend.add_fillcolors(shape, breaks, classvalues, **options)

        elif isinstance(layer, RasterLayer):
            shape = "polygon"
            # ...
            raise Exception("Legend layer for raster data not yet implemented")

    def add_fillsizes(self, layer, **options):
        if isinstance(layer, VectorLayer):
            if "Polygon" in layer.data.type:
                shape = "polygon"
            elif "Line" in layer.data.type:
                shape = "line"
            elif "Point" in layer.data.type:
                shape = "circle"
            else:
                raise Exception("Legend layer data must be of type polygon, linestring, or point")

            # add title automatically
            if not "title" in options and layer.name:
                options["title"] = layer.name

            # add any other nonvarying layer options
            options = dict(options)
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

        elif isinstance(layer, RasterLayer):
            raise Exception("Fillcolor is the only possible legend entry for a raster layer")

        

        

        
