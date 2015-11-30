
import random
import pyagg
import PIL, PIL.Image



class MapCanvas:
    def __init__(self, layers, width, height, background=None, *args, **kwargs):

        # remember and be remembered by the layergroup
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

    def zoom_factor(self, factor, center=None):
        self.drawer.zoom_factor(factor, center=center)

    def zoom_units(self, units, center=None):
        self.drawer.zoom_units(units, center=center)

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
                             coordspace_bbox=self.drawer.coordspace_bbox)
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


        


class LayerGroup:
    def __init__(self):
        self.layers = list()
        self.connected_maps = list()

    def __iter__(self):
        for layer in self.layers:
            yield layer

    def add_layer(self, layer):
        self.layers.append(layer)

    def move_layer(self, from_pos, to_pos):
        layer = self.layers.pop(from_pos)
        self.layers.insert(to_pos, layer)

    def remove_layer(self, position):
        self.layers.pop(position)

    def get_position(self, layer):
        return self.layers.index(layer)




class VectorLayer:
    def __init__(self, data, **options):
        
        self.data = data
        self.visible = True
        self.img = None
        
        # by default, set random style color
        rand = random.randrange
        randomcolor = (rand(255), rand(255), rand(255), 255)
        self.styleoptions = {"fillcolor": randomcolor}
            
        # override default if any manually specified styleoptions
        self.styleoptions.update(options)

    def render(self, width, height, coordspace_bbox):
        drawer = pyagg.Canvas(width, height, background=None)
        drawer.custom_space(*coordspace_bbox)
        # get features based on spatial index, for better speeds when zooming
        if not hasattr(self.data, "spindex"):
            self.data.create_spatial_index()
        spindex_features = self.data.quick_overlap(coordspace_bbox)
        # draw each as geojson, using same style options for all features
        for feat in spindex_features:
            drawer.draw_geojson(feat.geometry, **self.styleoptions)
        self.img = drawer.get_image()



        
class RasterLayer:
    def __init__(self, data, **options):
        self.data = data
        self.styleoptions = dict(**options)
        self.visible = True
        self.img = None

    def render(self, width, height, coordspace_bbox):
        # position in space
        positioned,mask = self.data.positioned(width, height, coordspace_bbox)

        # combine all data bands into one image for visualizing
        if len(positioned.bands) == 1:
            # greyscale if one band
            band1 = positioned.bands[0]
            img = band1.img.convert("RGB")
        else:
            # rgb of first three bands
            bands = [band.img for band in positioned.bands[:3] ]
            img = PIL.Image.merge("RGB", bands)

        # make edge and nodata mask transparent
        img.putalpha(mask)

        # final
        self.img = img


