
import random
import itertools
import pyagg, pyagg.legend
import PIL, PIL.Image
import colour

from .vector.data import VectorData
from .vector.loader import detect_filetype as vector_filetype
from .raster.data import RasterData
from .raster.loader import detect_filetype as raster_filetype



# TODO:
# all copys need to be systematically checked, not fully correct right now

DEFAULTSTYLE = "pastelle"

COLORSTYLES = dict([("strong", dict( [("intensity",1), ("brightness",0.5)]) ),
                    ("dark", dict( [("intensity",0.8), ("brightness",0.3)]) ),
                    ("matte", dict( [("intensity",0.4), ("brightness",0.5)]) ),
                    ("bright", dict( [("intensity",0.8), ("brightness",0.7)] ) ),
                    ("weak", dict( [("intensity",0.3), ("brightness",0.5)] ) ),
                    ("pastelle", dict( [("intensity",0.5), ("brightness",0.6)] ) )
                    ])

def Color(basecolor, intensity=None, brightness=None, opacity=None, style=None):
    """
    Returns an rgba color tuple of the color options specified.

    - basecolor: the human-like name of a color. Always required, but can also be set to 'random'. | string
    - *intensity: how strong the color should be. Must be a float between 0 and 1, or set to 'random' (by default uses the 'strong' style values, see 'style' below). | float between 0 and 1
    - *brightness: how light or dark the color should be. Must be a float between 0 and 1 , or set to 'random' (by default uses the 'strong' style values, see 'style' below). | float between 0 and 1
    - *style: a named style that overrides the brightness and intensity options (optional). | For valid style names, see below.

    Valid style names are:
    - 'strong'
    - 'dark'
    - 'matte'
    - 'bright'
    - 'pastelle'
    """
    # test if none
    if basecolor is None:
        return None
    
    # if already rgb tuple just return
    if isinstance(basecolor, (tuple,list)):
        rgb = [v / 255.0 for v in basecolor[:3]]
        if len(basecolor) == 3:
            rgba = list(colour.Color(rgb=rgb, saturation=intensity, luminance=brightness).rgb) + [opacity or 255]
        elif len(basecolor) == 4:
            rgba = list(colour.Color(rgb=rgb, saturation=intensity, luminance=brightness).rgb) + [opacity or basecolor[3]]
        rgba = [int(round(v * 255)) for v in rgba[:3]] + [rgba[3]]
        return tuple(rgba)
    
    #first check on intens/bright
    if not style and DEFAULTSTYLE:
        style = DEFAULTSTYLE
    if style and basecolor not in ("black","white","gray"):
        #style overrides manual intensity and brightness options
        intensity = COLORSTYLES[style]["intensity"]
        brightness = COLORSTYLES[style]["brightness"]
    else:
        #special black,white,gray mode, bc random intens/bright starts creating colors, so have to be ignored
        if basecolor in ("black","white","gray"):
            if brightness == "random":
                brightness = random.randrange(20,80)/100.0
        #or normal
        else:
            if intensity == "random":
                intensity = random.randrange(20,80)/100.0
            elif intensity is None:
                intensity = 0.7
            if brightness == "random":
                brightness = random.randrange(20,80)/100.0
            elif brightness is None:
                brightness = 0.5
    #then assign colors
    if basecolor in ("black","white","gray"):
        #graymode
        if brightness is None:
            rgb = colour.Color(color=basecolor).rgb
        else:
            #only listen to gray brightness if was specified by user or randomized
            col = colour.Color(color=basecolor)
            col.luminance = brightness
            rgb = col.rgb
    elif basecolor == "random":
        #random colormode
        basecolor = tuple([random.uniform(0,1), random.uniform(0,1), random.uniform(0,1)])
        col = colour.Color(rgb=basecolor)
        col.saturation = intensity
        col.luminance = brightness
        rgb = col.rgb
    elif isinstance(basecolor, (str,unicode)):
        #color text name
        col = colour.Color(basecolor)
        col.saturation = intensity
        col.luminance = brightness
        rgb = col.rgb
    else:
        #custom made color
        col = colour.Color(rgb=basecolor)
        col.saturation = intensity
        col.luminance = brightness
        rgb = col.rgb

    rgba = [int(round(v * 255)) for v in rgb] + [opacity or 255]
    return tuple(rgba)

    

class Layout:
    def __init__(self, width, height, background="white", title="", titleoptions=None, *args, **kwargs):

        # create a single map by default
        self.maps = []
        self.changed = True

        # create the drawer with a default percent space
        background = Color(background)
        self.drawer = pyagg.Canvas(width, height, background)
        self.drawer.percent_space() 

        # foreground layergroup for non-map decorations
        self.foregroundgroup = ForegroundLayerGroup()

        # title (these properties affect the actual rendered title after init)
        self.title = title
        self.titleoptions = titleoptions or dict()
        self.foregroundgroup.add_layer(Title(self))
            
        self.img = self.drawer.get_image()

    def add_map(self, mapobj, **pasteoptions):
        self.changed = True
        mapobj.pasteoptions = pasteoptions
        self.maps.append(mapobj)
        return mapobj

    def add_legend(self, legend=None, legendoptions=None, **pasteoptions):
        self.changed = True
        if not legend:
            # auto creates and builds legend based on first map (TODO: allow from other maps too)
            legendoptions = legendoptions or dict()
            legend = self.maps[0].get_legend(**legendoptions)
            
        legend.pasteoptions = pasteoptions
        self.foregroundgroup.add_layer(legend)
        return legend

##    def add_title(self, title, titleoptions=None, **pasteoptions):
##        # a little hacky, since uses pyagg label object directly,
##        # better if canvas could allow percent coord units
##        # ...
##        self.changed = True
##        override = titleoptions or dict()
##        titleoptions = dict(textsize=18)
##        titleoptions.update(override)
##        decor = pyagg.legend.Label(title, **titleoptions) # pyagg label indeed implements a render method()
##        defaultpaste = dict(xy=("50%w","1%h"), anchor="n")
##        defaultpaste.update(pasteoptions)
##        decor.pasteoptions = defaultpaste
##        decor.img = decor.render()
##        #print self.foreground,self.foreground._layers
##        self.foreground.add_layer(decor)

    def render_all(self, columns=None, rows=None, **kwargs):
        # render and draworder in one
        self.drawer.clear()

        if len(self.maps) == 1:
            mapobj = self.maps[0]
            mapobj.render_all()
            pasteoptions = mapobj.pasteoptions or dict(bbox=[5,5,95,95]) #dict(xy=("0%w","0%h")) #,"100%w","100%h"))
            self.drawer.paste(mapobj.img, **pasteoptions)

        elif len(self.maps) > 1:
            # grid all maps without any pasteoptions
            def mapimgs():
                for mapobj in self.maps:
                    if not mapobj.pasteoptions:
                        mapobj.render_all()
                        yield mapobj.img
            self.drawer.grid_paste(mapimgs(), columns=columns, rows=rows, **kwargs)
            
            # any remaining maps are pasted based on pasteoptions
            for mapobj in self.maps:
                if mapobj.pasteoptions:
                    mapobj.render_all()
                    self.drawer.paste(mapobj.img, **mapobj.pasteoptions)

        # foreground
        for layer in self.foregroundgroup:
            layer.render()
            if layer.img:
                pasteoptions = layer.pasteoptions.copy()
                if isinstance(layer, Title):
                    # since title is rendered on separate img then pasted,
                    # some titleoptions needs to be passed to pasteoptions
                    # instead of the rendering method
                    extraargs = dict([(k,self.titleoptions[k]) for k in ["xy","anchor"] if k in self.titleoptions])
                    pasteoptions.update(extraargs)
                self.drawer.paste(layer.img, **pasteoptions)
            
        self.img = self.drawer.get_image()

    def get_tkimage(self):
        # Special image format needed by Tkinter to display it in the GUI
        return self.drawer.get_tkimage()

    def view(self):
        if self.changed:
            self.render_all()
            self.changed = False
        self.drawer.view()

    def save(self, savepath):
        if self.changed:
            self.render_all()
            self.changed = False
        self.drawer.save(savepath)


class Map:
    def __init__(self, width=None, height=None, background=None, layers=None, title="", titleoptions=None, *args, **kwargs):

        # remember and be remembered by the layergroup
        if not layers:
            layers = LayerGroup()
        self.layers = layers
        layers.connected_maps.append(self)

        # background decorations
        self.backgroundgroup = BackgroundLayerGroup()
        if background:
            obj = Background(self)
            self.backgroundgroup.add_layer(obj)
        self.background = Color(background)

        # create the drawer with a default unprojected lat-long coordinate system
        # setting width and height locks the ratio, otherwise map size will adjust to the coordspace
        self.width = width or None
        self.height = height or None
        self.drawer = None
        self.zooms = []

        # foreground layergroup for non-map decorations
        self.foregroundgroup = ForegroundLayerGroup()

        # title (these properties affect the actual rendered title after init)
        self.title = title
        self.titleoptions = titleoptions or dict()
        self.foregroundgroup.add_layer(Title(self))

        self.dimensions = dict()
            
        self.img = None
        self.changed = True

    def _create_drawer(self):
        # get coordspace bbox aspect ratio of all layers
        autosize = not self.width or not self.height
        if self.width and self.height:
            pass
        elif self.layers.is_empty():
            self.height = 500 # default min height
            self.width = 1000 # default min width
        else:
            bbox = self.layers.bbox
            w,h = abs(bbox[0]-bbox[2]), abs(bbox[1]-bbox[3])
            aspect = w/float(h)
            if not self.width and not self.height:
                # largest side gets set to default minimum requirement
                if aspect < 1:
                    self.height = 500 # default min height
                else:
                    self.width = 1000 # default min width
                
            if self.width:
                self.height = int(self.width / float(aspect))
            elif self.height:
                self.width = int(self.height * aspect)
            
        # factor in zooms (zoombbx should somehow be crop, so alters overall img dims...)
        self.drawer = pyagg.Canvas(self.width, self.height, None)
        self.drawer.geographic_space()
        for zoom in self.zooms:
            zoom()
        # determine drawer pixel size based on zoom area
        # WARNING: when i changed this, it led to some funky misalignments...
        if autosize:
            bbox = self.drawer.coordspace_bbox
            w,h = abs(bbox[0]-bbox[2]), abs(bbox[1]-bbox[3])
            aspect = w/float(h)
            if aspect < 1:
                self.width = int(self.height * aspect)
            else:
                self.height = int(self.width / float(aspect))
            self.drawer.resize(self.width, self.height, lock_ratio=False)

    def copy(self):
        dupl = Map(self.width, self.height, background=self.background, layers=self.layers.copy())
        dupl.backgroundgroup = self.backgroundgroup.copy()
        if self.drawer: dupl.drawer = self.drawer.copy()
        dupl.foregroundgroup = self.foregroundgroup.copy()
        return dupl

    def pixel2coord(self, x, y):
        if not self.drawer: self._create_drawer() 
        return self.drawer.pixel2coord(x, y)

    # Map canvas alterations

    def offset(self, xmove, ymove):
        func = lambda: self.drawer.move(xmove, ymove)
        self.zooms.append(func)
        self.changed = True

    def resize(self, width, height):
        self.width = width
        self.height = height
        if not self.drawer: self._create_drawer()
        self.changed = True
        self.drawer.resize(width, height, lock_ratio=True)
        self.img = self.drawer.get_image()

    # Zooming

    def zoom_auto(self):
        bbox = self.layers.bbox
        func = lambda: self.zoom_bbox(*bbox)
        self.zooms.append(func)
        self.changed = True

    def zoom_bbox(self, xmin, ymin, xmax, ymax):
        if self.width and self.height:
            # predetermined map size will conor the aspect ratio
            func = lambda: self.drawer.zoom_bbox(xmin, ymin, xmax, ymax, lock_ratio=True)
        else:
            # otherwise snap zoom to edges so can determine map size from coordspace
            func = lambda: self.drawer.zoom_bbox(xmin, ymin, xmax, ymax, lock_ratio=False)
        self.zooms.append(func)
        self.changed = True

    def zoom_in(self, factor, center=None):
        func = lambda: self.drawer.zoom_in(factor, center=center)
        self.zooms.append(func)
        self.changed = True

    def zoom_out(self, factor, center=None):
        func = lambda: self.drawer.zoom_out(factor, center=center)
        self.zooms.append(func)
        self.changed = True

    def zoom_units(self, units, center=None):
        func = lambda: self.drawer.zoom_units(units, center=center)
        self.zooms.append(func)
        self.changed = True

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
        
##    def add_decoration(self, funcname, *args, **kwargs):
##        # draws directly on an image the size of the map canvas, so no pasteoptions needed
##        self.changed = True
##        decor = Decoration(self, funcname, *args, **kwargs)
##        decor.pasteoptions = dict() #xy=(0,0), anchor="nw")
##        self.foreground.add_layer(decor)

##    def add_grid(self, xinterval, yinterval, **kwargs):
##        self.drawer.draw_grid(xinterval, yinterval, **kwargs)
##
##    def add_axis(self, axis, minval, maxval, intercept,
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

    def get_legend(self, **legendoptions):
        legendoptions = legendoptions or dict()
        legend = Legend(self, **legendoptions)
        return legend

    def add_legend(self, legendoptions=None, **pasteoptions):
        self.changed = True
        legendoptions = legendoptions or {}
        legend = self.get_legend(**legendoptions)
        legend.pasteoptions = pasteoptions
        self.foregroundgroup.add_layer(legend)

    # Batch utilities

##    def add_dimension(self, dimtag, dimvalues):
##        self.dimensions[dimtag] = [(dimval,dimfunc,self)for dimval,dimfunc in dimvalues] # list of dimval-dimfunc pairs
##
##    def iter_dimensions(self, groupings=None):
##        # collect all dimensions from layers and the map itself as a flat list
##        alldimensions = dict()
##        for lyr in self:
##            if lyr.dimensions: 
##                alldimensions.update(lyr.dimensions) # note, duplicate dim names will be overwritten
##        alldimensions.update(self.dimensions)
##        
##        # yield all dimensions as all possible value combinations of each other
##        dimtagvalpairs = [[(dimtag,dimval) for dimval,dimfunc,dimparent in dimvalues] for dimtag,dimvalues in alldimensions.items()]
##        allcombis = itertools.product(*dimtagvalpairs)
##
##        def submapgen():
##            for dimcombi in allcombis:
##                # create the map and run all the functions for that combination
##                submap = self.copy()
##                for dimtag,dimval in dimcombi:
##                    dimfunc,dimparent = next(( (_dimfunc,_dimparent) for _dimval,_dimfunc,_dimparent in alldimensions[dimtag] if dimval == _dimval),None)  # first instance where dimval matches, same as dict lookup inside a list of keyval pairs
##                    if dimparent is self:
##                        dimfunc(submap)
##                    else:
##                        dimparent = dimparent.copy()
##                        dimfunc(dimparent)
##                dimdict = dict(dimcombi)
##                yield dimdict,submap
##                
##        if groupings:
##            # yield all grouped by each unique value combination belonging to the dimension names specified in groupings
##            # eg grouping by a region dimension will return groups of dimdict,submap for each unique value of region
##
##            def key(item):
##                dimdict,submap = item
##                keyval = [dimdict[gr] for gr in groupings]
##                return keyval
##            
##            for _id,dimcombis in itertools.groupby(sorted(submapgen(),key=key), key=key):
##                yield list(dimcombis) # list of dimdict,submap pairs belonging to same group
##
##        else:
##            # yield all flat, one by one
##            for dimdict,submap in submapgen():
##                yield dimdict,submap

    # Drawing

    def render_one(self, layer):
        self._create_drawer()
        
        if layer.visible:
            layer.render(width=self.drawer.width,
                         height=self.drawer.height,
                         bbox=self.drawer.coordspace_bbox)
            self.update_draworder()

    def render_all(self):
        self._create_drawer()
        
        for layer in self.backgroundgroup:
            layer.render()
        
        for layer in self.layers:
            if layer.visible:
                layer.render(width=self.drawer.width,
                             height=self.drawer.height,
                             bbox=self.drawer.coordspace_bbox)
                
                layer.render_text(width=self.drawer.width,
                                 height=self.drawer.height,
                                 bbox=self.drawer.coordspace_bbox)

        for layer in self.foregroundgroup:
            layer.render()
            
        self.changed = False
        self.update_draworder()

    def update_draworder(self):
        if not self.drawer: self._create_drawer()

        # paste the background decorations
        for layer in self.backgroundgroup:
            if layer.img:
                self.drawer.paste(layer.img, **layer.pasteoptions)

        # paste the map layers
        for layer in self.layers:
            if layer.visible and layer.img:
                self.drawer.paste(layer.img)

        # paste the map text/label layers
        for layer in self.layers:
            if layer.visible and layer.img_text:
                self.drawer.paste(layer.img_text)

        # paste the foreground decorations
        for layer in self.foregroundgroup:
            if layer.img:
                pasteoptions = layer.pasteoptions.copy()
                if isinstance(layer, Title):
                    # since title is rendered on separate img then pasted,
                    # some titleoptions needs to be passed to pasteoptions
                    # instead of the rendering method
                    extraargs = dict([(k,self.titleoptions[k]) for k in ["xy","anchor"] if k in self.titleoptions])
                    pasteoptions.update(extraargs)
                self.drawer.paste(layer.img, **pasteoptions)

        self.layers.changed = False
        self.img = self.drawer.get_image()

    def get_tkimage(self):
        # Special image format needed by Tkinter to display it in the GUI
        if not self.drawer: self._create_drawer() 
        return self.drawer.get_tkimage()

    def view(self):
        if self.changed:
            self.render_all()
        elif self.layers.changed:
            self.update_draworder()
        # make gui
        from . import app
        mapp = self
        win = app.builder.MultiLayerGUI(mapp)
        win.mainloop()

    def save(self, savepath):
        if self.changed:
            self.render_all()
        elif self.layers.changed:
            self.update_draworder()
        self.drawer.save(savepath)

        


class LayerGroup:
    def __init__(self):
        self._layers = list()
        self.connected_maps = list()
        self.dimensions = dict()
        self.changed = False

    def __iter__(self):
        for layer in self._layers:
            yield layer

    def __getitem__(self, i):
        return self._layers[i]

    def __setitem__(self, i, value):
        self.changed = True
        self._layers[i] = value

    def is_empty(self):
        return all((lyr.is_empty() for lyr in self))

    @property
    def bbox(self):
        if not self.is_empty():
            xmins,ymins,xmaxs,ymaxs = zip(*(lyr.bbox for lyr in self._layers if not lyr.is_empty() ))
            bbox = min(xmins),min(ymins),max(xmaxs),max(ymaxs)
            return bbox

        else:
            raise Exception("Cannot get bbox since there are no layers with geometries")

##    def add_dimension(self, dimtag, dimvalues):
##        # used by parent map to batch render all varieties of this layer
##        self.dimensions[dimtag] = dimvalues # list of dimval-dimfunc pairs

    def copy(self):
        layergroup = LayerGroup()
        layergroup._layers = list(self._layers)
        return layergroup

    def add_layer(self, layer, **options):
        self.changed = True
        
        if not isinstance(layer, (VectorLayer,RasterLayer)):
            # if data instance
            if isinstance(layer, VectorData):
                layer = VectorLayer(layer, **options)
            elif isinstance(layer, RasterData):
                layer = RasterLayer(layer, **options)
                
            # or if path string to data
            elif isinstance(layer, basestring):
                if vector_filetype(layer):
                    layer = VectorLayer(layer, **options)
                elif raster_filetype(layer):
                    layer = RasterLayer(layer, **options)
                else:
                    raise Exception("Filetype not supported")

            # invalid input
            else:
                raise Exception("Adding a layer requires either an existing layer instance, a data instance, or a filepath.")
            
        self._layers.append(layer)

        return layer

    def move_layer(self, from_pos, to_pos):
        self.changed = True
        layer = self._layers.pop(from_pos)
        self._layers.insert(to_pos, layer)

    def remove_layer(self, position):
        self.changed = True
        self._layers.pop(position)

    def get_position(self, layer):
        return self._layers.index(layer)





class BackgroundLayerGroup(LayerGroup):
    def add_layer(self, layer, **options):
        self._layers.append(layer, **options)

    def copy(self):
        background = BackgroundLayerGroup()
        background._layers = list(self._layers)
        return background





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
        self.img_text = None

        self.legendoptions = legendoptions or dict()
        self.nolegend = nolegend
        self.datafilter = datafilter
        
        # by default, set random style color
        randomcolor = Color("random")
        self.styleoptions = {"fillcolor": randomcolor,
                             "sortorder": "incr"}
            
        # override default if any manually specified styleoptions
        self.styleoptions.update(options)

        # set up symbol classifiers
        features = list(self.data) # classifications should be based on all features and not be affected by datafilter, thus enabling keeping the same classification across subsamples
        import classipy as cp
        for key,val in self.styleoptions.copy().items():
            if key in "fillcolor fillsize outlinecolor outlinewidth".split():
                if isinstance(val, dict):
                    # random colors if not specified in unique algo
                    if val["breaks"] == "unique" and "symbolvalues" not in val:
                        rand = random.randrange
                        val["symbolvalues"] = [Color("random")
                                                 for _ in range(20)]

                    # remove args that are not part of classipy
                    val = dict(val)
                    val["classvalues"] = val.pop("symbolvalues")
                    notclassified = val.pop("notclassified", None if "color" in key else 0) # this means symbol defaults to None ie transparent for colors and 0 for sizes if feature had a missing/null value, which should be correct
                    if "color" in key and notclassified != None:
                        notclassified = Color(notclassified)

                    # convert any text symbolvalues to pure numeric so can be handled by classipy
                    if "color" in key:
                        if isinstance(val["classvalues"], dict):
                            # value color dict mapping for unique breaks
                            val["classvalues"] = dict([(k,Color(v)) for k,v in val["classvalues"].items()])
                        else:
                            # color gradienr
                            val["classvalues"] = [Color(col) for col in val["classvalues"]]
                    else:
                        pass #val["classvalues"] = [Unit(col) for col in val["classvalues"]]

                    # cache precalculated values in id dict
                    # more memory friendly alternative is to only calculate breakpoints
                    # and then find classvalue for feature when rendering,
                    # which is likely slower
                    classifier = cp.Classifier(features, **val)
                    self.styleoptions[key] = dict(classifier=classifier,
                                                   symbols=dict((id(f),classval) for f,classval in classifier),
                                                   notclassified=notclassified
                                                   )
                    
                elif hasattr(val, "__call__"):
                    pass
                
                else:
                    # convert any text symbolvalues to pure numeric so can be handled by classipy
                    if "color" in key:
                        val = Color(val)
                    else:
                        pass #val = Unit(val)
                    self.styleoptions[key] = val

        # set up text classifiers
        import classipy as cp
        if "text" in self.styleoptions and "textoptions" in self.styleoptions:
            for key,val in self.styleoptions["textoptions"].copy().items():
                if isinstance(val, dict):
                    # random colors if not specified in unique algo
                    if val["breaks"] == "unique" and "symbolvalues" not in val:
                        rand = random.randrange
                        val["symbolvalues"] = [Color("random")
                                                 for _ in range(20)]

                    # remove args that are not part of classipy
                    val = dict(val)
                    val["classvalues"] = val.pop("symbolvalues")
                    notclassified = val.pop("notclassified", None if "color" in key else 0) # this means symbol defaults to None ie transparent for colors and 0 for sizes if feature had a missing/null value, which should be correct

                    # cache precalculated values in id dict
                    # more memory friendly alternative is to only calculate breakpoints
                    # and then find classvalue for feature when rendering,
                    # which is likely slower
                    classifier = cp.Classifier(features, **val)
                    self.styleoptions["textoptions"][key] = dict(classifier=classifier,
                                                               symbols=dict((id(f),classval) for f,classval in classifier),
                                                               notclassified=notclassified
                                                               )
                else:
                    self.styleoptions["textoptions"][key] = val

    def is_empty(self):
        """Used for external callers unaware of the vector or raster nature of the layer"""
        return not self.has_geometry()

    def has_geometry(self):
        return any((feat.geometry for feat in self.features()))

    def copy(self):
        new = VectorLayer(self.data)
        new.visible = self.visible
        new.img = self.img.copy() if self.img else None
        new.img_text = self.img_text.copy() if self.img_text else None

        new.legendoptions = self.legendoptions
        new.nolegend = self.nolegend
        new.datafilter = self.datafilter
        
        new.styleoptions = self.styleoptions.copy()

        return new
    
    @property
    def bbox(self):
        if self.has_geometry():
            xmins, ymins, xmaxs, ymaxs = itertools.izip(*(feat.bbox for feat in self.features() if feat.geometry))
            bbox = min(xmins),min(ymins),max(xmaxs),max(ymaxs)
            return bbox
        else:
            raise Exception("Cannot get bbox since there are no selected features with geometries")

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
        if self.has_geometry():
            if not bbox:
                bbox = self.bbox

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
                if "shape" in self.styleoptions: rendict["shape"] = self.styleoptions["shape"]
                for key in "fillcolor fillsize outlinecolor outlinewidth".split():
                    if key in self.styleoptions:
                        val = self.styleoptions[key]
                        if isinstance(val, dict):
                            # lookup self in precomputed symboldict
                            fid = id(feat)
                            if fid in val["symbols"]:
                                rendict[key] = val["symbols"][fid]
                            else:
                                rendict[key] = val["notclassified"]
                        elif hasattr(val, "__call__"):
                            rendict[key] = val(feat)
                        else:
                            rendict[key] = val

                # draw
                drawer.draw_geojson(feat.geometry, **rendict)
                
            self.img = drawer.get_image()

        else:
            self.img = None

    def render_text(self, width, height, bbox=None, lock_ratio=True, flipy=False):
        if self.has_geometry() and self.styleoptions.get("text"):

            textkey = self.styleoptions["text"]
            
            if not bbox:
                bbox = self.bbox

            if flipy:
                bbox = bbox[0],bbox[3],bbox[2],bbox[1]
            
            drawer = pyagg.Canvas(width, height, background=None)
            drawer.custom_space(*bbox, lock_ratio=lock_ratio)

            
            features = self.features(bbox=bbox)

            # custom draworder (sortorder is only used with sortkey)
            if "sortkey" in self.styleoptions:
                features = sorted(features, key=self.styleoptions["sortkey"],
                                  reverse=self.styleoptions["sortorder"].lower() == "decr")

            # draw each as text
            for feat in features:
                text = textkey(feat)
                
                if text is not None:
                
                    # get symbols
                    rendict = dict()
                    if "textoptions" in self.styleoptions:
                        for key,val in self.styleoptions["textoptions"].copy().items():
                            if isinstance(val, dict):
                                # lookup self in precomputed symboldict
                                fid = id(feat)
                                if fid in val["symbols"]:
                                    rendict[key] = val["symbols"][fid]
                                else:
                                    rendict[key] = val["notclassified"]
                            elif hasattr(val, "__call__"):
                                rendict[key] = val(feat)
                            else:
                                rendict[key] = val

                    # draw
                    # either bbox or xy can be set for positioning
                    if "bbox" not in rendict:
                        # default to xy being centroid, but also allow other options or custom key
                        rendict["xy"] = rendict.get("xy", "centroid")
                        if rendict["xy"] == "centroid":
                            rendict["xy"] = feat.get_shapely().centroid.coords[0]
                    drawer.draw_text(text, **rendict)
                
            self.img_text = drawer.get_image()

        else:
            self.img_text = None



        
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

    @property
    def bbox(self):
        return self.data.bbox

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
        # TODO: maybe instead do:   img.putalpha(self.rendered.mask)
        # ...

        # final
        self.img = img


class Legend:
    def __init__(self, map, autobuild=True, **options):
        self.map = map
        self.img = None
        self.autobuild = autobuild
        self._legend = pyagg.legend.Legend(refcanvas=map.drawer, **options)

    def add_fillcolors(self, layer, **override):
        if isinstance(layer, VectorLayer):
            # use layer's legendoptions and possibly override
            options = dict(layer.legendoptions)
            options.update(override)

            shape = options.pop("shape", None)
            shape = shape or layer.styleoptions.get("shape")
            if not shape:
                shape = self._get_layer_shape(layer)

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
                    classvalues = cls.classvalues_interp

                # add any other nonvarying layer options
                for k in "fillsize outlinecolor outlinewidth".split():
                    if k not in options and k in layer.styleoptions:
                        v = layer.styleoptions[k]
                        if not isinstance(v, dict):
                            options[k] = v

                #print options
                self._legend.add_fillcolors(shape, breaks, classvalues, **options)

            else:
                # add as static symbol if none of the dynamic ones
                self.add_single_symbol(shape, **options)

        elif isinstance(layer, RasterLayer):
            shape = "polygon"
            # ...
            raise Exception("Legend layer for raster data not yet implemented")

    def add_fillsizes(self, layer, **override):
        if isinstance(layer, VectorLayer):
            # use layer's legendoptions and possibly override
            options = dict(layer.legendoptions)
            options.update(override)
            options["fillcolor"] = options.get("fillcolor") # so that if there is no fillcolor, should use empty sizes

            shape = options.pop("shape", None)
            shape = shape or layer.styleoptions.get("shape")
            if not shape:
                shape = self._get_layer_shape(layer)
            
            if "fillsize" in layer.styleoptions and isinstance(layer.styleoptions["fillsize"], dict):
                
                # add any other nonvarying layer options
                #print 9999
                #print options
                for k in "fillcolor outlinecolor outlinewidth".split():
                    #print k
                    if k not in options and k in layer.styleoptions:
                        v = layer.styleoptions[k]
                        #print k,v,type(v)
                        if not isinstance(v, dict):
                            options[k] = v
                            
                #print options

                cls = layer.styleoptions["fillsize"]["classifier"]
                self._legend.add_fillsizes(shape, cls.breaks, cls.classvalues_interp, **options)

            else:
                # add as static symbol if none of the dynamic ones
                self.add_single_symbol(shape, **options)

        elif isinstance(layer, RasterLayer):
            raise Exception("Fillsize is not a possible legend entry for a raster layer")

    def add_single_symbol(self, layer, **override):
        if isinstance(layer, VectorLayer):
            # use layer's legendoptions and possibly override
            options = dict(layer.legendoptions)
            options.update(override)
            options.update(layer.styleoptions)

            shape = options.pop("shape", self._get_layer_shape(layer))

            if "title" in options:
                options["label"] = options.pop("title")
            if "titleoptions" in options:
                options["labeloptions"] = options.pop("titleoptions")

            if not "fillsize" in options:
                options["fillsize"] = "2%min"

            self._legend.add_symbol(shape, **options)

        elif isinstance(layer, RasterLayer):
            raise Exception("Not yet implemented")


    def _get_layer_shape(self, layer):
        if isinstance(layer, VectorLayer):
            if "Polygon" in layer.data.type:
                shape = "polygon"
            elif "Line" in layer.data.type:
                shape = "line"
            elif "Point" in layer.data.type:
                shape = "circle"
            else:
                raise Exception("Legend layer data must be of type polygon, linestring, or point")

            return shape

        elif isinstance(layer, RasterLayer):
            raise Exception("_get_layer_shape is only meant for vector data, not raster data")

    def _autobuild(self):
        # maybe somehow clear itself in case autobuild and rendering multiple times for updating
        # ...
        
        # build the legend automatically
        for layer in self.map:
            if not layer.nolegend:
                # Todo: better handling when more than one classipy option for same layer
                # perhaps grouping into basegroup under same layer label
                # ...
                anydynamic = False
                if "fillcolor" in layer.styleoptions and isinstance(layer.styleoptions["fillcolor"], dict):
                    # is dynamic and should be highlighted specially
                    #print 999,layer,layer.legendoptions
                    self.add_fillcolors(layer, **layer.legendoptions)
                    anydynamic = True
                if "fillsize" in layer.styleoptions and isinstance(layer.styleoptions["fillsize"], dict):
                    # is dynamic and should be highlighted specially
                    self.add_fillsizes(layer, **layer.legendoptions)
                    anydynamic = True
                    
                # add as static symbol if none of the dynamic ones
                if not anydynamic:
                    self.add_single_symbol(layer, **layer.legendoptions)

    def render(self):
        # ensure the drawer is created so pyagg legend can use it to calculate sizes etc
        if not self.map.drawer:
            self.map._create_drawer()
        self._legend.refcanvas = self.map.drawer
        # render it
        if self.autobuild:
            self._autobuild()
        rendered = self._legend.render()
        self.img = rendered.get_image()



class Background:
    def __init__(self, map):
        self.map = map
        self.img = None
        self.pasteoptions = dict()

    def render(self):
        canv = pyagg.Canvas(self.map.drawer.width, self.map.drawer.height, self.map.background)
        self.img = canv.get_image()



class Title:
    def __init__(self, layout):
        self.layout = layout
        self.img = None
        self.pasteoptions = dict(xy=("50%w","1%h"), anchor="n")

    def render(self):
        if self.layout.title:
            # since title is rendered on separate img then pasted,
            # some titleoptions needs to be passed to pasteoptions
            # instead of the rendering method
            titleoptions = self.layout.titleoptions.copy()
            titleoptions.pop("xy", None)
            titleoptions.pop("anchor", None)
            rendered = pyagg.legend.Label(self.layout.title, **titleoptions).render() # pyagg label indeed implements a render method()
            self.img = rendered.get_image()



##class Decoration:
##    def __init__(self, map, funcname, *args, **kwargs):
##        self.map = map
##        
##        self.funcname = funcname
##        self.args = args
##        self.kwargs = kwargs
##
##        self.img = None
##        
##    def render(self):
##        drawer = pyagg.Canvas(self.map.drawer.width, self.map.drawer.height, background=None)
##        drawer.custom_space(*self.map.drawer.coordspace_bbox)
##        func = getattr(drawer,self.funcname)
##        func(*self.args, **self.kwargs)
##        self.img = drawer.get_image()
        

        
