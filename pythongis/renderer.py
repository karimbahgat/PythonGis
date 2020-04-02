
import os
import math
import random
import itertools
import pyagg, pyagg.legend
import PIL, PIL.Image, PIL.ImageChops, PIL.ImageMath, PIL.ImageDraw, PIL.ImagePath
import colour

import shapely, shapely.geometry

import classypie as cp

import pycrs

from .vector.data import VectorData
from .vector.loader import detect_filetype as vector_filetype
from .raster.data import RasterData
from .raster.loader import detect_filetype as raster_filetype



# TODO:
# - all copys need to be systematically checked, not fully correct right now
# - unspecified outlinewidth in layer styleoptions becomes weird in legend, but ok if specified. 

DEFAULTSTYLE = None

COLORSTYLES = dict([("strong", dict( [("intensity",1.5), ("brightness",1.0)]) ),
                    ("weak", dict( [("intensity",0.3), ("brightness",0.8)] ) ),
                    ("dark", dict( [("intensity",1.2), ("brightness",0.5)]) ),
                    ("bright", dict( [("intensity",1.2), ("brightness",1.5)] ) ),
                    ("matte", dict( [("intensity",0.8), ("brightness",0.95)]) ),
                    ("pastelle", dict( [("intensity",0.7), ("brightness",1.4)] ) )
                    ])

class ColorPalette(object):
    def __init__(self, name):
        self.name = name
        self.colors = {'dynamic-qual': ['dodgerblue','darkorange','limegreen','crimson','slateblue','saddlebrown','hotpink','gray','yellowgreen','turquoise'],
                       'dynamic-seq': ["lightblue","dodgerblue","midnightblue"], #['thistle','crimson','darkred'],
                       'dynamic-div': [],
                       'dynamic-cycl': [],
                       }[name]
        self.cur = 0

    def __call__(self, *args, **kwargs):
        if self.cur >= len(self.colors):
            self.cur = 0
        i = self.cur
        self.cur += 1
        return self.colors[i]

    def get(self, i):
        # TODO: should probably figure way to interpolate and get gradient...
        # ...
        return self.colors[i]

COLORGEN = ColorPalette('dynamic-qual')

def rgb(basecolor, intensity=None, brightness=None, opacity=None, style=None):
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
            #elif intensity is None:
            #    intensity = 0.7
            if brightness == "random":
                brightness = random.randrange(20,80)/100.0
            #elif brightness is None:
            #    brightness = 0.5
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
        if intensity != None:
            intensity = min(1, col.saturation * intensity)
            col.saturation = intensity
        if brightness != None:
            brightness = min(1, col.luminance * brightness)
            col.luminance = brightness
        rgb = col.rgb
    elif isinstance(basecolor, (str,unicode)):
        #color text name
        replacenames = {'blue':'dodgerblue','orange':'darkorange','green':'limegreen','red':'crimson','purple':'slateblue','brown':'saddlebrown','pink':'hotpink'}
        basecolor = replacenames.get(basecolor, basecolor)
        col = colour.Color(basecolor)
        if intensity != None:
            intensity = min(1, col.saturation * intensity)
            col.saturation = intensity
        if brightness != None:
            brightness = min(1, col.luminance * brightness)
            col.luminance = brightness
        rgb = col.rgb
    else:
        #custom made color
        col = colour.Color(rgb=basecolor)
        if intensity != None:
            intensity = min(1, col.saturation * intensity)
            col.saturation = intensity
        if brightness != None:
            brightness = min(1, col.luminance * brightness)
            col.luminance = brightness
        rgb = col.rgb

    rgba = [int(round(v * 255)) for v in rgb] + [opacity or 255]
    return tuple(rgba)

def get_crs_transformer(fromcrs, tocrs):
    if not (fromcrs and tocrs):
        return None
    
    if isinstance(fromcrs, basestring):
        fromcrs = pycrs.parse.from_unknown_text(fromcrs)

    if isinstance(tocrs, basestring):
        tocrs = pycrs.parse.from_unknown_text(tocrs)

    fromcrs = fromcrs.to_proj4()
    tocrs = tocrs.to_proj4()
    
    if fromcrs != tocrs:
        import pyproj
        fromcrs = pyproj.Proj(fromcrs)
        tocrs = pyproj.Proj(tocrs)
        def _isvalid(p):
            x,y = p
            return not (math.isinf(x) or math.isnan(x) or math.isinf(y) or math.isnan(y))
        def _project(points):
            xs,ys = itertools.izip(*points)
            xs,ys = pyproj.transform(fromcrs,
                                     tocrs,
                                     xs, ys)
            newpoints = list(itertools.izip(xs, ys))
            newpoints = [p for p in newpoints if _isvalid(p)] # drops inf and nan
            return newpoints
    else:
        _project = None

    return _project

def reproject_bbox(bbox, transformer, sampling_freq=20):
    x1,y1,x2,y2 = bbox
    w,h = x2-x1, y2-y1
    sampling_freq = int(sampling_freq)
    dx,dy = w/float(sampling_freq), h/float(sampling_freq)
    gridsamples = [(x1+dx*ix,y1+dy*iy)
                   for iy in range(sampling_freq+1)
                   for ix in range(sampling_freq+1)]
    gridsamples = transformer(gridsamples)
    if not gridsamples:
        return None
    xs,ys = zip(*gridsamples)
    xmin,ymin,xmax,ymax = min(xs),min(ys),max(xs),max(ys)
    bbox = [xmin,ymin,xmax,ymax] 
    #print 'bbox transform',bbox
    return bbox


###########

class Layout:
    def __init__(self, width, height, background="white", title="", titleoptions=None, *args, **kwargs):

        # create a single map by default
        self.maps = []
        self.changed = True

        # create the drawer with a default percent space
        background = rgb(background)
        self.drawer = pyagg.Canvas(width, height, background)
        self.drawer.percent_space() 

        # foreground layergroup for non-map decorations
        self.foregroundgroup = ForegroundLayerGroup()

        # title (these properties affect the actual rendered title after init)
        self.title = title
        self.titleoptions = dict(textsize="6%w")
        if titleoptions: self.titleoptions.update(titleoptions)
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

        legend.pasteoptions.update(pasteoptions)
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

    def render_all(self, columns=None, rows=None, antialias=False, **kwargs):
        # render and draworder in one
        self.drawer.clear()

        if len(self.maps) == 1:
            mapobj = self.maps[0]
            mapobj.render_all(antialias=antialias)
            pasteoptions = mapobj.pasteoptions or dict(bbox=[5,5,95,95]) #dict(xy=("0%w","0%h")) #,"100%w","100%h"))
            self.drawer.paste(mapobj.img, **pasteoptions)

        elif len(self.maps) > 1:
            # grid all maps without any pasteoptions
            def mapimgs():
                for mapobj in self.maps:
                    if not mapobj.pasteoptions:
                        mapobj.render_all(antialias=antialias)
                        yield mapobj.img
            self.drawer.grid_paste(mapimgs(), columns=columns, rows=rows, **kwargs)
            
            # any remaining maps are pasted based on pasteoptions
            for mapobj in self.maps:
                if mapobj.pasteoptions:
                    mapobj.render_all(antialias=antialias)
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

    def view(self, **kwargs):
        if self.changed:
            self.render_all(**kwargs)
            self.changed = False
        self.drawer.view()

    def save(self, savepath, **kwargs):
        if self.changed:
            self.render_all(antialias=True, **kwargs)
            self.changed = False
        self.drawer.save(savepath)


class Map:
    def __init__(self, width=None, height=None, background=None, layers=None, title="", titleoptions=None, textoptions=None, ppi=300, crs=None, *args, **kwargs):

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
        self.background = rgb(background)

        # create the drawer with a default unprojected lat-long coordinate system
        # setting width and height locks the ratio, otherwise map size will adjust to the coordspace
        self.width = width or None
        self.height = height or None
        self.ppi = ppi
        self.drawer = None
        self.textoptions = textoptions or dict()

        crs = crs or '+proj=longlat +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +nodef'
        if isinstance(crs, basestring):
            crs = pycrs.parse.from_unknown_text(crs)
        self.crs = crs

        # foreground layergroup for non-map decorations
        self.foregroundgroup = ForegroundLayerGroup()

        # title (these properties affect the actual rendered title after init)
        self.title = title
        self.titleoptions = titleoptions or {}
        self.foregroundgroup.add_layer(Title(self))

        self.dimensions = dict()
            
        self.img = None
        self.changed = True

        #self.drawer = pyagg.Canvas(self.width, self.height, (111,111,111))
        #self.drawer.geographic_space()

    def _create_drawer(self):
        # get coordspace bbox aspect ratio of all layers
        autosize = not self.width or not self.height
        if self.width and self.height:
            pass
        elif self.layers.is_empty():
            self.height = 500 # default min height
            self.width = 1000 # default min width
        else:
            bbox = self.layers.bbox(self.crs)
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
            
        # create drawer
        self.drawer = pyagg.Canvas(self.width, self.height, None, ppi=self.ppi)
        self.drawer.textoptions.update(self.textoptions)

        # by default zoom to full world
        xmin,ymax,xmax,ymin = -180,90,180,-90
        
        # transform if necessary
        fromcrs = pycrs.parse.from_proj4('+proj=longlat +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +nodef')
        _transform = get_crs_transformer(fromcrs, self.crs)
        if _transform:
            bbox = reproject_bbox([xmin,ymin,xmax,ymax], _transform)
            if not bbox:
                raise Exception('Could not determine global bbox of the given map crs, all coordinates were out of bounds in the target crs (inf or nan)')
            xmin,ymin,xmax,ymax = bbox

        self.drawer.custom_space(xmin, ymax, xmax, ymin, lock_ratio=True) # assume inverted y axis.....

    def copy(self):
        dupl = Map(self.width, self.height, background=self.background, layers=self.layers.copy(),
                   title=self.title, titleoptions=self.titleoptions, textoptions=self.textoptions,
                   ppi=self.ppi, crs=self.crs)
        dupl.backgroundgroup = self.backgroundgroup.copy()
        if self.drawer: dupl.drawer = self.drawer.copy()
        if self.img: dupl.img = self.img.copy()
        dupl.foregroundgroup = self.foregroundgroup.copy()
        return dupl

    def pixel2coord(self, x, y):
        if not self.drawer: self._create_drawer() 
        return self.drawer.pixel2coord(x, y)

    # Map canvas alterations

    def offset(self, xmove, ymove, geographic=False):
        if not self.drawer: self._create_drawer()
        if geographic:
            raise NotImplementedError('Offsetting map by geographic coords not yet implemented')
        self.drawer.move(xmove, ymove)
        #self.zooms.append(func)
        self.changed = True
        if self.img:
            self.img = self.drawer.get_image()

    def resize(self, width, height):
        self.width = width
        self.height = height
        if not self.drawer: self._create_drawer()
        self.changed = True
        self.drawer.resize(width, height, lock_ratio=True)
        if self.img:
            self.img = self.drawer.get_image()

    def crop(self, xmin, ymin, xmax, ymax, geographic=False):
        if not self.drawer: self._create_drawer()
        if geographic:
            raise NotImplementedError('Cropping map by geographic coords not yet implemented')
        self.changed = True
        self.drawer.crop(xmin,ymin,xmax,ymax)
        self.width = self.drawer.width
        self.height = self.drawer.height
        if self.img:
            self.img = self.drawer.get_image()

    # Zooming

    @property
    def bbox(self):
        if not self.drawer: self._create_drawer()
        return list(self.drawer.coordspace_bbox)

    def zoom_auto(self):
        if not self.drawer: self._create_drawer()
        bbox = self.layers.bbox(self.crs)
        self.zoom_bbox(*bbox)
        #self.zooms.append(func)
        self.changed = True
        # NOTE: no need to update img here, already done in zoom_bbox

    def zoom_bbox(self, xmin, ymin, xmax, ymax, geographic=False):
        if not self.drawer: self._create_drawer()
        #print 'zoom bbox', xmin, ymin, xmax, ymax

        if geographic:
            # bbox is in geographic coords, transform to map crs bbox
            fromcrs = pycrs.parse.from_proj4('+proj=longlat +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +nodef')
            _transform = get_crs_transformer(fromcrs, self.crs)
            if _transform:
                bbox = reproject_bbox([xmin,ymin,xmax,ymax], _transform)
                if not bbox:
                    raise Exception('Geographic bbox could not be reprojected to target crs, all coordinates were out of bounds (inf or nan)')
                xmin,ymin,xmax,ymax = bbox

        #print 'zoom bbox', xmin, ymin, xmax, ymax

        # perform zoom
        if self.width and self.height:
            # predetermined map size will honor the aspect ratio
            self.drawer.zoom_bbox(xmin, ymin, xmax, ymax, lock_ratio=True)
        else:
            # otherwise snap zoom to edges so can determine map size from coordspace
            self.drawer.zoom_bbox(xmin, ymin, xmax, ymax, lock_ratio=False)
            
        #self.zooms.append(func)
        self.changed = True
        if self.img:
            self.img = self.drawer.get_image()

    def zoom_in(self, factor, center=None):
        if not self.drawer: self._create_drawer()
        self.drawer.zoom_in(factor, center=center)
        #func = lambda: self.drawer.zoom_in(factor, center=center)
        #self.zooms.append(func)
        self.changed = True
        if self.img:
            self.img = self.drawer.get_image()

    def zoom_out(self, factor, center=None):
        if not self.drawer: self._create_drawer()
        self.drawer.zoom_out(factor, center=center)
        #func = lambda: self.drawer.zoom_out(factor, center=center)
        #self.zooms.append(func)
        self.changed = True
        if self.img:
            self.img = self.drawer.get_image()

    def zoom_units(self, units, center=None, geographic=False):
        if not self.drawer: self._create_drawer()
        if geographic:
            from .vector._helpers import _vincenty_distance
            desired_km = units
            x1,y1,x2,y2 = self.drawer.coordspace_bbox
            xs = [x1,x2]
            ys = [y1,y2]
            xmin,ymin,xmax,ymax = min(xs),min(ys),max(xs),max(ys)
            # transform to geographic coord bbox
            tocrs = pycrs.parse.from_proj4('+proj=longlat +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +nodef')
            _transform = get_crs_transformer(self.crs, tocrs)
            if _transform:
                bbox = reproject_bbox([xmin,ymin,xmax,ymax], _transform)
                if not bbox:
                    raise Exception('Could not reproject map crs bbox to geographic bbox, all coordinates were out of bounds (inf or nan)')
                xmin,ymin,xmax,ymax = bbox
            cur_km = _vincenty_distance((ymin,xmin), (ymin,xmax))
            ratio = desired_km/cur_km
            if ratio < 1: ratio = -1/ratio
            ratio = -ratio
            #units = unit_width * ratio # transformed
            #print units
        #self.drawer.zoom_units(units, center=center)
        self.drawer.zoom_factor(ratio)
        #print _vincenty_distance((y1,x1), (y1,x1+self.drawer.coordspace_width))
        #self.zooms.append(func)
        self.changed = True
        if self.img:
            self.img = self.drawer.get_image()

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
        legend.pasteoptions.update(pasteoptions)
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

    def render_one(self, layer, antialias=True, update_draworder=True):
        if not self.drawer: self._create_drawer()
        
        if layer.visible: 
            layer.render(width=self.drawer.width,
                         height=self.drawer.height,
                         bbox=self.drawer.coordspace_bbox,
                         antialias=antialias,
                         crs=self.crs)
            layer.render_text(width=self.drawer.width,
                             height=self.drawer.height,
                             bbox=self.drawer.coordspace_bbox,
                             crs=self.crs,
                             default_textoptions=self.textoptions)
            if update_draworder:
                self.update_draworder()

    def render_all(self, antialias=True):
        #import time
        #t=time.time()
        if not self.drawer: self._create_drawer()
        #print "# createdraw",time.time()-t

        #import time
        #t=time.time()
        
        for layer in self.backgroundgroup:
            layer.render()
        
        for layer in self.layers:
            self.render_one(layer, antialias=antialias, update_draworder=False)

        for layer in self.foregroundgroup:
            layer.render()
        #print "# rendall",time.time()-t
            
        self.changed = False
        import time
        t=time.time()
        self.update_draworder()
        print "# draword",time.time()-t

    def update_draworder(self):
        if self.drawer: self.drawer.clear()
        else: self.drawer = self._create_drawer()

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
        #return self.drawer.get_tkimage()
        import PIL, PIL.ImageTk
        #img = PIL.Image.open("C:/Users/kimo/Desktop/best/2017-02-26 044.jpg")
        return PIL.ImageTk.PhotoImage(image=self.img)
        
##        if not hasattr(self, "_tkim"):
##            print "new"
##            import PIL.ImageTk
##            self._tkim = PIL.ImageTk.PhotoImage(self.drawer.img)
##        self._tkim.paste(self.drawer.img)
##        return self._tkim
        
##        if not hasattr(self, "_tkim"):
##            print "new"
##            import Tkinter
##            self._tkim = Tkinter.PhotoImage(self.drawer.img)
##        dat = list(self.drawer.img.getdata())
##        rows = (dat[self.drawer.width*i:self.drawer.width*(i+1)] for i in range(self.drawer.height))
##        data = ('{' + ' '.join(("#%02x%02x%02x" % rgb[:3] for rgb in row)) + '}' for row in rows)
##        self._tkim.put(' '.join(data))
##        return self._tkim

    def view(self):
        mapp = self.copy() # ???
        # make gui
        from . import app
        win = app.builder.SimpleMapViewerGUI(mapp)
        win.mainloop()

    def save(self, savepath, meta=False, **kwargs):
        if not self.img:
            self.render_all(antialias=True) # antialias
        if meta:
            # save image + affine file + prj file if necessary (as if a georeferenced raster)
            r = RasterData(image=self.img, crs=self.crs) 
            r.set_geotransform(affine=self.drawer.coordspace_invtransform) # inverse bc the drawer actually goes from coords -> pixels, we need pixels -> coords
            r.save(savepath, **kwargs)
        else:
            # save image only
            #self.drawer.save(savepath) # kwargs not currently supported in pyagg
            self.drawer.drawer.flush()
            self.drawer.img.save(savepath, **kwargs)

        


class LayerGroup:
    def __init__(self):
        self._layers = list()
        self.connected_maps = list()
        self.dimensions = dict()
        self.changed = False

    def __iter__(self):
        for layer in self._layers:
            yield layer

    def __len__(self):
        return len(self._layers)

    def __getitem__(self, i):
        return self._layers[i]

    def __setitem__(self, i, value):
        self.changed = True
        self._layers[i] = value

    def is_empty(self):
        return all((lyr.is_empty() for lyr in self))

    def bbox(self, crs=None):
        '''
        - crs: if specified, bboxes from layers with different crs will be converted to a single common crs. 
        '''
        if not self.is_empty():
            #xmins,ymins,xmaxs,ymaxs = zip(*(lyr.bbox for lyr in self._layers if not lyr.is_empty() ))
            bboxes = []
            for lyr in self._layers:
                if not lyr.is_empty():
                    bbox = lyr.data.bbox

                    # transform bbox to common crs
                    _transform = get_crs_transformer(lyr.data.crs, crs)
                    if _transform:
                        bbox = reproject_bbox(bbox, _transform)
                        if not bbox:
                            # out of bounds, simply ignore
                            continue

                    bboxes.append(bbox)

            xmins,ymins,xmaxs,ymaxs = zip(*bboxes)
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




def initSharedData(datadict):
    print 'initfunc'
    global sharedData
    sharedData = datadict

def parallel_vecrend(features, width, height, bbox, styleoptions, antialias=True):

    import time
    t=time.time()

    print 'hello'

    #self = sharedData['data']
    
    drawer = pyagg.Canvas(width, height, background=None)
    drawer.custom_space(*bbox, lock_ratio=True)

    #features = self.features(bbox=bbox)

    # custom draworder (sortorder is only used with sortkey)
    if "sortkey" in styleoptions:
        features = sorted(features, key=styleoptions["sortkey"],
                          reverse=styleoptions["sortorder"].lower() == "decr")

    # prep PIL if non-antialias polygon
    if 1: #not antialias and "Polygon" in self.data.type:
        #print "preint",time.time()-t
        import time
        t=time.time()
        img = PIL.Image.new("RGBA", (width,height), None)
        PIL_drawer = PIL.ImageDraw.Draw(img)   #self.PIL_drawer

    # for each
    for row,geometry in features:
        
        # get symbols
        rendict = dict()
        if "shape" in styleoptions: rendict["shape"] = styleoptions["shape"]
        for key in "fillcolor fillsize outlinecolor outlinewidth".split():
            if key in styleoptions:
                val = styleoptions[key]
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

        # fast PIL Approach for non-antialias polygons
        if not antialias and "Polygon" in geometry["type"]:

            if "Multi" in geometry["type"]:
                geoms = geometry["coordinates"]
            else:
                geoms = [geometry["coordinates"]]

            fill = tuple((int(c) for c in rendict["fillcolor"])) if rendict.get("fillcolor") else None
            outline = tuple((int(c) for c in rendict["outlinecolor"])) if rendict.get("outlinecolor") else None
            
            for poly in geoms:
                coords = poly[0]
                if len(poly) > 1:
                    holes = poly[1:0]
                else:
                    holes = []

                # first exterior
                path = PIL.ImagePath.Path([tuple(p) for p in coords])
                path.transform(drawer.coordspace_transform)
                #print "draw",str(path.tolist())[:300]
                path.compact(1)
                #print "draw",str(path.tolist())[:100]
                if len(path) > 1:
                    PIL_drawer.polygon(path, fill, None)
                    PIL_drawer.line(path, outline, 1)

                # then holes
                for hole in holes:
                    path = PIL.ImagePath.Path([tuple(p) for p in hole])
                    path.transform(drawer.coordspace_transform)
                    path.compact(1)
                    if len(path) > 1:
                        PIL_drawer.polygon(path, (0,0,0,0), None)
                        PIL_drawer.line(path, outline, 1)

        else:
            # high qual geojson
            drawer.draw_geojson(geometry, **rendict)

    # flush
    print "internal",time.time()-t
    if 1: #not antialias and "Polygon" in self.data.type:
        img = img
    else:
        img = drawer.get_image()

##    # transparency
##    if self.transparency:
##        opac = 256 - int(256*(self.transparency/100.0))
##        
##        r,g,b,a = self.img.split()
##        a = PIL.ImageMath.eval('min(alpha,opac)', alpha=a, opac=opac).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
##        self.img.putalpha(a)
##        
##    # effects
##    for eff in self.effects:
##        self.img = eff(self)

    #img.show()

    return None




class VectorLayer:
    def __init__(self, data, legendoptions=None, legend=True, datafilter=None, transparency=0, flipy=True, **options):
        """
        UNFINISHED docstring...
        
            flipy (optional): If True, flips the direction of the y-coordinate axis so that it increases towards the top of the screen
                instead of the bottom of the screen. This is useful for rendering unprojected long/lat coordinates and is the default. 
                Should only be changed to False when rendering projected x/y coordinates, whose y-axis typically increases towards the bottom.
        """

        if not isinstance(data, VectorData):
            # assume data is filepath
            dtoptions = options.get("dataoptions", dict())
            data = VectorData(data, **dtoptions)
        
        self.data = data
        self.visible = True
        self.transparency = transparency
        self.flipy = flipy
        self.img = None
        self.img_text = None

        self.effects = []

        self.legendoptions = legendoptions or dict(title='Vector Layer')
        self.legend = legend
        self.datafilter = datafilter
        
        # by default, get next color from color generator
        col = COLORGEN()
        self.styleoptions = {"fillcolor": col,
                             "outlinewidth": 0.13,
                             "sortorder": "incr"}
        if 'Line' in self.data.type:
            self.styleoptions['outlinecolor'] = None
            
        # override default if any manually specified styleoptions
        self.styleoptions.update(options)

        # make sure has geom
        if not self.data.has_geometry():
            return

        # classify
        self.update()

    def update(self):
        # set up symbol classifiers
        features = list(self.data) # classifications should be based on all features and not be affected by datafilter, thus enabling keeping the same classification across subsamples
        for key,val in self.styleoptions.copy().items():
            if key in "fillcolor fillopacity fillsize outlinecolor outlinewidth".split():
                if isinstance(val, dict):
                    # natural breaks if not specified
                    if "breaks" not in val:
                        val['breaks'] = 'natural'
                        
                    # default colors if not specified
                    if "color" in key and "colors" not in val:
                        if val["breaks"] == "unique":
                            colgen = ColorPalette('dynamic-qual')
                            val["colors"] = [colgen() for _ in range(10)]
                        else:
                            colgen = ColorPalette('dynamic-seq')
                            val["colors"] = [colgen.get(0), colgen.get(1), colgen.get(2)]

                    # remove args that are not part of classypie
                    val = dict(val)
                    if isinstance(val.get("key"), basestring):
                        fieldname = val["key"]
                        val["key"] = lambda f,fn=fieldname: f[fn] # turn field name into callable
                    if "color" in key:
                        val["classvalues"] = val.pop("colors")
                    elif "size" in key:
                        val["classvalues"] = val.pop("sizes")
                    elif "opacity" in key:
                        val["classvalues"] = val.pop("opacities")

                    notclassified = val.pop("notclassified", None if "color" in key else 0) # this means symbol defaults to None ie transparent for colors and 0 for sizes if feature had a missing/null value, which should be correct
                    if "color" in key and notclassified != None:
                        notclassified = rgb(notclassified)

                    # convert any color names to pure numeric so can be handled by classypie
                    if "color" in key:
                        if isinstance(val["classvalues"], dict):
                            # value color dict mapping for unique breaks
                            val["classvalues"] = dict([(k,rgb(v)) for k,v in val["classvalues"].items()])
                        else:
                            # color gradient
                            val["classvalues"] = [rgb(col) for col in val["classvalues"]]
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

                    # convert from area to radius for more correct visual comparisons
                    # first interpolation was done between areas, now convert to radius sizes
                    # TODO: now only circles, test and calc for other shapes too
                    if 'size' in key and 'Point' in self.data.type:
                        shp = self.styleoptions.get('shape')
                        if shp is None or shp == 'circle':
                            #val['classvalues'] = [math.sqrt(v/math.pi) for v in val['classvalues']]
                            classifier.classvalues_interp = [math.sqrt(v/math.pi) for v in classifier.classvalues_interp]
                            self.styleoptions[key]['symbols'] = dict((id(f),classval) for f,classval in classifier)
                    
                elif hasattr(val, "__call__"):
                    pass
                
                else:
                    # convert any color names to pure numeric so can be handled by classypie
                    if "color" in key:
                        val = rgb(val)
                    elif "size" in key:
                        #pass #val = Unit(val)
                        # convert from area to radius for more correct visual comparisons
                        # TODO: now only circles, test and calc for other shapes too
                        if 'Point' in self.data.type:
                            shp = self.styleoptions.get('shape')
                            if shp is None or shp == 'circle':
                                val = math.sqrt(val/math.pi)
                    elif "opacity" in key:
                        val = val

                    self.styleoptions[key] = val

        # set up text classifiers
        if "text" in self.styleoptions and "textoptions" in self.styleoptions:
            for key,val in self.styleoptions["textoptions"].copy().items():
                if isinstance(val, dict):
                    # random colors if not specified in unique algo
                    if "color" in key and "colors" not in val:
                        if val["breaks"] == "unique":
                            val["colors"] = [rgb("random") for _ in range(20)]
                        else:
                            val["colors"] = [rgb("random"),rgb("random")]

                    # remove args that are not part of classypie
                    val = dict(val)
                    if isinstance(val.get("key"), basestring):
                        fieldname = val["key"]
                        val["key"] = lambda f,fn=fieldname: f[fn] # turn field name into callable
                    if "color" in key:
                        val["classvalues"] = val.pop("colors")
                    else:
                        val["classvalues"] = val.pop("sizes")
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

                    
                elif hasattr(val, "__call__"):
                    pass
                
                else:
                    # convert any color names to pure numeric so can be handled by classypie
                    if "color" in key:
                        val = rgb(val)
                    else:
                        pass #val = Unit(val)
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
        new.legend = self.legend
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

    def add_effect(self, effect, **kwargs):
        
        if isinstance(effect, basestring):

            if effect == "shadow":
                def effect(lyr):
                    _,a = lyr.img.convert('LA').split()
                    opacity = kwargs.get('opacity', 0.777) # dark/strong shadow
                    a = a.point(lambda v: v*opacity) 
                    binary = PIL.Image.new('L', lyr.img.size, 0) # black
                    binary.putalpha(a)
                    drawer = pyagg.canvas.from_image(binary)
                    #binary = lyr.img.point(lambda v: 255 if v > 0 else 0)
                    #drawer = pyagg.canvas.from_image(binary)
                    #drawer.replace_color((255,255,255,255), kwargs.get("color", (115,115,115,155)))
                    drawer.move(kwargs.get("xdist"), kwargs.get("ydist"))
                    drawer.paste(lyr.img)
                    img = drawer.get_image()
                    return img

            elif effect == "glow":

                def effect(lyr):
                    import PIL, PIL.ImageMorph

                    _,a = lyr.img.convert('LA').split()
                    binary = a.point(lambda v: 255 if v > 0 else 0)
                    #binary.show()
                    
                    color = kwargs.get("color")
                    if isinstance(color, list):
                        # use gradient to set range of colors via incremental grow/shrink
                        newimg = PIL.Image.new("RGBA", lyr.img.size, (0,0,0,0))
                        grad = pyagg.canvas.Gradient(color)
                        for col in grad.interp(kwargs.get("size")):
                            col = tuple(col)
                            _,binary = PIL.ImageMorph.MorphOp(op_name="dilation8").apply(binary)
                            _,edge = PIL.ImageMorph.MorphOp(op_name="edge").apply(binary)
                            if len(col) == 4:
                                edge = edge.point(lambda v: col[3] if v == 255 else 0)
                            newimg.paste(col[:3], (0,0), mask=edge)
                        newimg.paste(lyr.img, (0,0), mask=lyr.img)
                    else:
                        # entire area same color
                        for _ in range(kwargs.get("size")):
                            _,binary = PIL.ImageMorph.MorphOp(op_name="dilation8").apply(binary)
                        newimg = PIL.Image.new("RGBA", lyr.img.size, (0,0,0,0))
                        newimg.paste(color, (0,0), mask=binary)
                        newimg.paste(lyr.img, (0,0), mask=lyr.img)
                        
                    return newimg
                
            elif effect == "inner":
                # TODO: gets affected by previous effects, somehow only get original rendered image
                # TODO: should do inner type on each feature, not the entire layer.
                # OR: effect for entire layer, and separate for each feature via styleoptions...?
                # TODO: canvas edge should not be counted...
                # TODO: transp gradient not working, sees through even original layer...

                # WARNING: DOESNT REALLY WORK CORRECTLY...
                    
                def effect(lyr):
                    import PIL, PIL.ImageMorph
                    
                    _,a = lyr.img.convert('LA').split()
                    binary = a.point(lambda v: 255 if v > 0 else 0)
                    #binary.show()
                    
                    color = kwargs.get("color")
                    if isinstance(color, list):
                        # use gradient to set range of colors via incremental grow/shrink
                        newimg = lyr.img.copy()
                        grad = pyagg.canvas.Gradient(color)
                        for col in grad.interp(kwargs.get("size")):
                            col = tuple(col)
                            _,binary = PIL.ImageMorph.MorphOp(op_name="erosion8").apply(binary)
                            _,edge = PIL.ImageMorph.MorphOp(op_name="edge").apply(binary)
                            if len(col) == 4:
                                edge = edge.point(lambda v: col[3] if v == 255 else 0)
                            newimg.paste(col[:3], (0,0), mask=edge)
                    else:
                        # entire area same color
                        for _ in range(kwargs.get("size")):
                            _,binary = PIL.ImageMorph.MorphOp(op_name="erosion8").apply(binary)
                        newimg = PIL.Image.new("RGBA", lyr.img.size, (0,0,0,0))
                        newimg.paste(color, (0,0), mask=lyr.img)
                        newimg.paste(lyr.img, (0,0), mask=binary)
                        
                    return newimg
                
            else:
                raise Exception("Not a valid effect")
        
        self.effects.append(effect)

    def add_text_effect(self, effect, **kwargs):
        raise NotImplementedError

    def render(self, width, height, bbox=None, crs=None, antialias=True):
        '''
        - bbox: bounding box of the coordsys to be rendered (defaults to data bbox). 
        - crs: if specified, determines the coordsys to be renderered (defaults to data crs). 
        '''

        # normal way
        if self.has_geometry():
            import time
            t=time.time()

            # get on-the-fly projection transformer (only if specified and different)
            if isinstance(crs, basestring):
                crs = pycrs.parse.from_unknown_text(crs)
            _transform = get_crs_transformer(self.data.crs, crs)

            # unless specified, bbox is taken from the data and converted to the crs if necessary
            if not bbox:
                bbox = self.bbox

                # determine map space by projecting data bounds
                if _transform:
                    bbox = reproject_bbox(bbox, _transform)
                    if not bbox:
                        # data extent is out of bounds for map crs, exit early
                        self.img = None
                        return

            # create the drawer within the bbox coordsys
            drawer = pyagg.Canvas(width, height, background=None)
            drawer.custom_space(*bbox, lock_ratio=True)

            if not antialias:
                drawer.drawer.setantialias(False)

            # update the bbox to the calculated drawer bbox (slightly different due to the aspect ratio of the canvas size)
            bbox = drawer.coordspace_bbox

            # get features inside map extent
            if _transform:
                # transform from projected map space back to data coordinates
                _itransform = get_crs_transformer(crs, self.data.crs)
                bbox = reproject_bbox(bbox, _itransform)
                if not bbox:
                    # map extent is out of bounds for data crs, exit early
                    self.img = None
                    return
                    
            features = self.features(bbox=bbox)

            # custom draworder (sortorder is only used with sortkey)
            if "sortkey" in self.styleoptions:
                features = sorted(features, key=self.styleoptions["sortkey"],
                                  reverse=self.styleoptions["sortorder"].lower() == "decr")
    
            # for each
            for feat in features:

                # reproject
                if _transform:
                    #print 'text pre fbox',feat.bbox, feat.get_shapely().centroid.coords[0]
                    feat = feat.copy()
                    feat.transform(_transform)
                    if not feat.geometry:
                        continue
                    #print 'text post fbox',feat.bbox, feat.get_shapely().centroid.coords[0]
                
                # get symbols
                rendict = dict()
                if "shape" in self.styleoptions: rendict["shape"] = self.styleoptions["shape"]
                for key in "fillcolor fillopacity fillsize outlinecolor outlinewidth".split():
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

                # set fillcolor opacity
                fillopacity = rendict.get('fillopacity', None)
                fillcolor = rendict.get('fillcolor', None)
                if fillopacity != None and fillcolor != None:
                    fillcolor = tuple(fillcolor[:3]) + (fillopacity*255,)
                    rendict['fillcolor'] = fillcolor

                # draw
                drawer.draw_geojson(feat.geometry, **rendict)

            # flush
            print "internal",time.time()-t
            self.img = drawer.get_image()

            # transparency
            if self.transparency:
                #opac = 256 - int(256*(self.transparency/100.0))
                opac = 1 - self.transparency
                
                r,g,b,a = self.img.split()
                #a = PIL.ImageMath.eval('min(alpha,opac)', alpha=a, opac=opac).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
                a = PIL.ImageMath.eval('float(alpha) * opac', alpha=a, opac=opac).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
                self.img.putalpha(a)
                
            # effects
            for eff in self.effects:
                self.img = eff(self)

        else:
            self.img = None

    def render_text(self, width, height, bbox=None, crs=None, antialias=True, default_textoptions=None):
        
        if self.styleoptions.get("text") and self.has_geometry():
            import time
            t=time.time()

            textkey = self.styleoptions["text"]

            # get on-the-fly projection transformer (only if specified and different)
            if isinstance(crs, basestring):
                crs = pycrs.parse.from_unknown_text(crs)
            _transform = get_crs_transformer(self.data.crs, crs)

            # unless specified, bbox is taken from the data and converted to the crs if necessary
            if not bbox:
                bbox = self.bbox

                # determine map space by projecting data bounds
                if _transform:
                    bbox = reproject_bbox(bbox, _transform)
                    if not bbox:
                        # data extent is out of bounds for map crs, exit early
                        self.img_text = None
                        return

            # create the drawer within the bbox coordsys
            drawer = pyagg.Canvas(width, height, background=None)
            drawer.textoptions.update(default_textoptions)
            drawer.custom_space(*bbox, lock_ratio=True)

            if not antialias:
                drawer.drawer.setantialias(False)

            # update the bbox to the calculated drawer bbox (slightly different due to the aspect ratio of the canvas size)
            bbox = drawer.coordspace_bbox

            # get features inside map extent
            if _transform:
                # transform from projected map space back to data coordinates
                _itransform = get_crs_transformer(crs, self.data.crs)
                bbox = reproject_bbox(bbox, _itransform)
                if not bbox:
                    # map extent is out of bounds for data crs, exit early
                    self.img_text = None
                    return
            features = self.features(bbox=bbox)

            # custom draworder (sortorder is only used with sortkey)
            if "sortkey" in self.styleoptions:
                features = sorted(features, key=self.styleoptions["sortkey"],
                                  reverse=self.styleoptions["sortorder"].lower() == "decr")

            # get map bbox shp, to crop to map window for text placement
            mx1,my1,mx2,my2 = drawer.coordspace_bbox
            mxmin,mymin = min(mx1,mx2), min(my1,my2)
            mxmax,mymax = max(mx1,mx2), max(my1,my2)
            mapshp = shapely.geometry.box(mxmin,mymin,mxmax,mymax)

            # draw each as text 
            for feat in features:
                text = textkey(feat)
                
                if text is not None:

                    # reproject
                    # FIND WAY TO REUSE THE TRANSFORM FROM THE render(), CURRENTLY TRANSFORMS TWICE
                    if _transform:
                        #print 'text pre fbox',feat.bbox, feat.get_shapely().centroid.coords[0]
                        feat = feat.copy()
                        feat.transform(_transform)
                        if not feat.geometry:
                            continue
                        #print 'text post fbox',feat.bbox, feat.get_shapely().centroid.coords[0]
                
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
                        # also allow custom key for any of the options
                        for k,v in rendict.items():
                            if hasattr(v, "__call__"):
                                rendict[k] = v(feat)
                        # default to xy being centroid
                        rendict["xy"] = rendict.get("xy", "centroid")
                        if rendict["xy"] == "centroid":
                            shp = feat.get_shapely()
                            # TODO: CROPPING TO MAP WINDOW NOT WORKING YET
                            #print 77,shp.bounds, mapshp.bounds
                            #xy = shp.intersection(mapshp).centroid.coords[0]
                            try:
                                xy = shp.intersection(mapshp).centroid.coords[0]
                            except:
                                xy = shp.centroid.coords[0]
                            rendict["xy"] = xy

                        elif rendict["xy"] == "midpoint":
                            # midpoint of bbox
                            # crop to map window by taking intersection of bboxes
                            # TODO: Only consider single geom bboxes
                            xmin,ymin,xmax,ymax = feat.bbox
                            xmin,ymin = max(xmin,mxmin), max(ymin,mymin)
                            xmax,ymax = min(xmax,mxmax), min(ymax,mymax)
                            rendict["xy"] = (xmin+xmax)/2.0, (ymin+ymax)/2.0

                        elif hasattr(rendict["xy"], '__call__'):
                            rendict["xy"] = rendict["xy"](feat)
                                
                    drawer.draw_text(text, **rendict)

            # flush
            print "internal text",time.time()-t
            self.img_text = drawer.get_image()

            # transparency
            if self.transparency:
                #opac = 256 - int(256*(self.transparency/100.0))
                opac = 1 - self.transparency
                
                r,g,b,a = self.img_text.split()
                #a = PIL.ImageMath.eval('min(alpha,opac)', alpha=a, opac=opac).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
                a = PIL.ImageMath.eval('float(alpha) * opac', alpha=a, opac=opac).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
                self.img_text.putalpha(a)

        else:
            self.img_text = None



        
class RasterLayer:
    def __init__(self, data, legendoptions=None, legend=True, transparency=0, **options):
        
        if not isinstance(data, RasterData):
            # assume data is filepath
            doptions = options.get("dataoptions", dict())
            data = RasterData(data, **doptions)
        
        self.data = data
        self.visible = True
        self.transparency = transparency
        self.img = None
        self.img_text = None

        # TODO: allow setting the crs...

        self.effects = []

        self.legendoptions = legendoptions or dict(title='Raster Layer')
        self.legend = legend

        # by default, set random style color
        if not "type" in options:
            if len(data.bands) >= 3:
                options["type"] = "rgb"
            else:
                options["type"] = "colorscale"

        # auto cutoff bottom/top 0.1 percent outliers if big nrs and min/max not already set
        # TODO: Now, only for big float and int data, maybe instead do some optimal distribution/outlier checking.
        # TODO: How to prevent hiding values for binary or other small-range rasters?
        # TODO: Maybe don't autoset to avoid confusion, instead having to set manually. 
        if self.data.mode in 'float32 float16 int32 int16' and ('maxval' not in options or "minval" not in options):
            pass #options["cutoff"] = options.get("cutoff", (0.1,99.9))

        # stretching
        if options["type"] in ("grayscale","colorscale"):
            options["bandnum"] = options.get("bandnum", 0)
            band = self.data.bands[options["bandnum"]]
            
            if "cutoff" in options:

                mincut,maxcut = options["cutoff"]

                # ALT1: cumulative count percentages
                #print options
                
                #pxcounts = band.img.histogram() #mask=band.mask)
                #pxcounts = [(c,v) for c,v in pxcounts if v != band.nodataval]
                
                #vals = (cell.value for cell in band if cell.value != band.nodataval)
                #from collections import Counter
                #pxcounts = ((c,v) for v,c in Counter(vals).items())
                #pxcounts = sorted(pxcounts, key=lambda(c,v): v)

                pxcounts = band.img.getcolors(band.width*band.height)
                pxcounts = ((c,v) for c,v in pxcounts if v != band.nodataval)
                pxcounts = sorted(pxcounts, key=lambda(c,v): v)
                tot = sum((c for c,v in pxcounts))

                if 'minval' not in options:
                    cumul = 0
                    for count,val in pxcounts:
                        cumul += count
                        prog = cumul / float(tot) * 100
                        #print val,count,cumul,prog
                        if prog >= mincut:
                            options["minval"] = val
                            break

                if 'maxval' not in options:
                    cumul = 0
                    for count,val in pxcounts:
                        cumul += count
                        prog = cumul / float(tot) * 100
                        #print val,count,cumul,prog
                        if prog >= maxcut:
                            options["maxval"] = val
                            break

                #print options           

                # ALT2: value range percent, no frequency counting
##                print options
##                sortedvals = sorted(set((v for v in band.img.getdata() if v != band.nodataval)))
##
##                i1 = len(sortedvals) * mincut/100.0
##                if i1.is_integer():
##                    options["minval"] = sortedvals[int(i1)]
##                else:
##                    frac = i1 - int(i1)
##                    diff = sortedvals[int(i1+1)] - sortedvals[int(i1)] 
##                    options["minval"] = sortedvals[int(i1)] + (diff * frac)
##
##                i2 = len(sortedvals) * maxcut/100.0
##                if i2.is_integer():
##                    options["maxval"] = sortedvals[int(i2)]
##                else:
##                    frac = i2 - int(i2)
##                    diff = sortedvals[int(i2+1)] - sortedvals[int(i2)] 
##                    options["maxval"] = sortedvals[int(i2)] + (diff * frac)
##
##                print options

                # ALT3: percent of min max range, fast but not meaningful
                #rng = options["maxval"] - options["minval"]
                #options["maxval"] = options["minval"] + rng / 100.0 * maxcut
                #options["minval"] += rng / 100.0 * mincut
            
            # retrieve min and maxvals from data if not manually specified
            if not "minval" in options:
                options["minval"] = band.summarystats("min")["min"]
            if not "maxval" in options:
                options["maxval"] = band.summarystats("max")["max"]

            # optionally center so that min and max are equal distance from a given midpoint
            if "center" in options:
                center = options["center"]
                mindiff = abs(options["minval"] - center)
                maxdiff = abs(options["maxval"] - center)
                diff = max(mindiff, maxdiff)
                options["minval"] = center - diff
                options["maxval"] = center + diff

        # set colors
        if options['type'] == 'grayscale':

            # process gradient
            options["gradcolors"] = [rgb("black"),rgb("white")]

        elif options['type'] == 'colorscale':

            # process gradient
            if "gradcolors" in options:
                options["gradcolors"] = [rgb(col) for col in options["gradcolors"]]
            else:
                options["gradcolors"] = [rgb("blue"),rgb("turquoise"),rgb("green"),rgb("yellow"),rgb("red")]

        elif options["type"] == "rgb":
            options["r"] = options.get("r", 0)
            options["g"] = options.get("g", 1)
            options["b"] = options.get("b", 2)
            
        # remember style settings
        self.styleoptions = options

    @property
    def bbox(self):
        return self.data.bbox

    def is_empty(self):
        return False # for now

    def render(self, resampling="nearest", antialias=True, crs=None, **georef):
        # position in space

        # get projection transformer (only if specified and different)
        if not isinstance(crs, pycrs.CS):
            crs = pycrs.parse.from_unknown_text(crs)
        _transform = get_crs_transformer(self.data.crs, crs)
        
        if _transform:
            # on-the-fly reproject to given crs
            try:
                rendered = self.data.manage.reproject(crs, resampling, **georef)
            # out of bounds
            except:
                self.img = None
                return
        else:
            # get bbox from data if not specified
            if "bbox" not in georef:
                georef["bbox"] = self.data.bbox

            # normal affine resample
            try:
                rendered = self.data.resample(method=resampling, **georef)
            except:
                # out of bounds
                self.img = None
                return

        # TODO: binary 1bit rasters dont show correctly
        # ...

        if self.styleoptions["type"] == "grayscale":
            
            # Note: Maybe remove and instead must specify white and black in colorscale type...?
            # ...
            
            band = rendered.bands[self.styleoptions["bandnum"]]
            mask = band.mask
            
            # equalize
            minval,maxval = self.styleoptions["minval"], self.styleoptions["maxval"]
            if None not in (minval,maxval):
                valrange = maxval-minval
                if valrange:
                    expr = "(convert(val,'F') - {minval}) / {valrange} * 255".format(minval=minval,valrange=valrange)
                    band.compute(expr)
                else:
                    band.compute("0")
            else:
                band.compute("0")
            # colorize
            img = band.img.convert("LA")

        elif self.styleoptions["type"] == "colorscale":
            band = rendered.bands[self.styleoptions["bandnum"]]
            mask = band.mask
            
            # equalize
            minval,maxval = self.styleoptions["minval"], self.styleoptions["maxval"]
            if None not in (minval,maxval):
                valrange = maxval-minval
                if valrange:
                    expr = "(convert(val,'F') - {minval}) / {valrange} * 255".format(minval=minval,valrange=valrange)
                    band.compute(expr)
                else:
                    band.compute("0")
            else:
                band.compute("0")
            # colorize
            canv = pyagg.canvas.from_image(band.img.convert("RGBA"))
            canv = canv.color_remap(self.styleoptions["gradcolors"])
            img = canv.get_image()

        elif self.styleoptions["type"] == "rgb":
            mask = rendered.mask
            
            rband = rendered.bands[self.styleoptions["r"]].img.convert("L")
            gband = rendered.bands[self.styleoptions["g"]].img.convert("L")
            bband = rendered.bands[self.styleoptions["b"]].img.convert("L")
            img = PIL.Image.merge("RGB", [rband,gband,bband])
            #rendered.bands[self.styleoptions["r"]].img.show()
            #rendered.bands[self.styleoptions["g"]].img.show()
            #rendered.bands[self.styleoptions["b"]].img.show()
            #img.show()
            #fdsfdsf
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

        #img.paste(0, mask=rendered.mask) # sets all bands to 0 incl the alpha band
        #print img, rendered.mask, rendered.mask.histogram()
        #rendered.mask.save('rendmask.png')
        #print "rendmask",rendered.mask
        #img.save("prealph.png")
        
        ###OLDONE: #img.putalpha(PIL.ImageChops.invert(mask.convert("L"))) # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
        
        r,g,b,a = img.split()
        invmask = PIL.ImageChops.invert(mask.convert("L"))
        newalpha = PIL.ImageMath.eval('min(alpha,invmask)', alpha=a, invmask=invmask).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
        img.putalpha(newalpha)
        
        #img.save("postalph.png")
        # ...

        # final
        self.img = img
        
        # transparency
        if self.transparency:
            #opac = int(256*self.transparency)
            #opac = 256 - int(256*self.transparency)
            opac = 1 - self.transparency
            
            r,g,b,a = self.img.split()
            #a = PIL.ImageMath.eval('min(alpha,opac)', alpha=a, opac=opac).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
            #a = PIL.ImageMath.eval('max(alpha,opac)', alpha=a, opac=opac).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
            a = PIL.ImageMath.eval('float(alpha) * opac', alpha=a, opac=opac).convert('L') # putalpha img must be 0 to make it transparent, so the nodata mask must be inverted
            #print a, a.getextrema()
            self.img.putalpha(a)
            #self.img = PIL.Image.merge('RGBA', [r,g,b,a])

    def render_text(self, resampling="nearest", crs=None, **georef):
        self.img_text = None


class Legend:
    def __init__(self, map, layers=None, autobuild=True, **options):
        self.map = map
        self.layers = layers or []
        self.img = None
        self.autobuild = autobuild
        self.options = options
        self.pasteoptions = dict(xy=("2%w","98%h"), anchor="sw")
        self._legend = pyagg.legend.Legend(refcanvas=map.drawer, **self.options)

    def add_fillcolors(self, layer, **override):
        # use layer's legendoptions and possibly override
        options = dict(layer.legendoptions)
        options.update(override)
            
        if isinstance(layer, VectorLayer):
            shape = options.pop("shape", None)
            shape = shape or layer.styleoptions.get("shape")
            if not shape:
                shape = self._get_layer_shape(layer)

            if "fillcolor" in layer.styleoptions and isinstance(layer.styleoptions["fillcolor"], dict):
                cls = layer.styleoptions["fillcolor"]["classifier"]

                # force legend type depending on classifier algorithm
                if cls.algo == "unique": options["valuetype"] = "categorical"
                elif cls.algo == "proportional": options["valuetype"] = "proportional"

                # detect valuetype
                if options.get("valuetype") == "categorical":
                    # WARNING: not very stable yet...
                    categories = set((cls.key(item),tuple(classval)) for item,classval in cls) # only the unique keys
                    breaks,classvalues = zip(*sorted(categories, key=lambda e:e[0]))
                elif options.get("valuetype") == "proportional":
                    breaks = options.get("ticks", cls.breaks)
                    classvalues = cls.classvalues_interp
                    options["length"] = options.get("length", "40%min")
                    options["thickness"] = options.get("thickness", "4%min")
                    options["direction"] = options.get("direction", "e")
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
            if layer.styleoptions["type"] in ("grayscale","colorscale"):
                if layer.styleoptions["type"] == "grayscale":
                    gradient = [rgb("black"),rgb("white")]
                else:
                    gradient = layer.styleoptions["gradcolors"]
                options["ticks"] = options.get("ticks", [layer.styleoptions["minval"], layer.styleoptions["maxval"]])
                options["length"] = options.get("length", "40%min")
                options["thickness"] = options.get("thickness", "4%min")
                options["direction"] = options.get("direction", "e")
                self._legend.add_fillcolors(shape=None, breaks=options["ticks"], classvalues=gradient,
                                            valuetype="proportional",
                                            **options)

    def add_fillsizes(self, layer, **override):
        if isinstance(layer, VectorLayer):
            # use layer's legendoptions and possibly override
            options = dict(layer.legendoptions)
            options.update(override)
            #options["fillcolor"] = options.get("fillcolor") # so that if there is no fillcolor, should use empty sizes

            shape = options.pop("shape", None)
            shape = shape or layer.styleoptions.get("shape")
            if not shape:
                shape = self._get_layer_shape(layer)
            
            if "fillsize" in layer.styleoptions and isinstance(layer.styleoptions["fillsize"], dict):
                cls = layer.styleoptions["fillsize"]["classifier"]

                # force legend type depending on classifier algorithm
                if cls.algo == "unique": options["valuetype"] = "categorical"
                elif cls.algo == "proportional": options["valuetype"] = "proportional"

                if options.get("valuetype") == "proportional":
                    # switch, uses classvalues as breaks
                    breaks = cls.breaks
                    classvalues = cls.classvalues_interp
                else:
                    breaks = cls.breaks
                    classvalues = cls.classvalues_interp
                
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
                self._legend.add_fillsizes(shape, breaks, classvalues, **options)

            else:
                # add as static symbol if none of the dynamic ones
                self.add_single_symbol(shape, **options)

        elif isinstance(layer, RasterLayer):
            raise Exception("Fillsize is not a possible legend entry for a raster layer")

    def add_single_symbol(self, layer, **override):
        if isinstance(layer, VectorLayer):
            # use layer's legendoptions and possibly override
            options = dict(layer.styleoptions)
            options.update(layer.legendoptions)
            options.update(override)

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
        self._legend = pyagg.legend.Legend(refcanvas=self.map.drawer, **self.options)
        
        # build the legend automatically
        # either based on all map layers with the legend flag
        # or based on specified layer instances, even if legend flag is off
        layers = self.layers or [l for l in self.map if l.legend]
        for layer in layers:
            if isinstance(layer, VectorLayer):
                # Todo: better handling when more than one classypie option for same layer
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

            elif isinstance(layer, RasterLayer):
                if layer.styleoptions["type"] in ("grayscale","colorscale"):
                    self.add_fillcolors(layer, **layer.legendoptions)

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
            titleoptions = dict(textsize="3%w", padding=0.32)
            titleoptions.update(self.layout.titleoptions.copy())
            titleoptions.pop("xy", None)
            titleoptions.pop("anchor", None)
            boxoptions = dict(fillcolor=titleoptions.pop('fillcolor','white'),
                              outlinecolor=titleoptions.pop('outlinecolor','black'),
                              outlinewidth=titleoptions.pop('outlinewidth','5%min'),
                              )
            rendered = pyagg.legend.BaseGroup(refcanvas=self.layout.drawer, title=self.layout.title, titleoptions=titleoptions, **boxoptions).render() # pyagg label indeed implements a render method()
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
        

        
