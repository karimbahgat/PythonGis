
# Import GUI functionality
import Tkinter as tk
from tkFileDialog import askopenfilenames, asksaveasfilename
from .buttons import *
from .popups import *
from .progbar import *

# Import style
from . import theme
style_layerspane_normal = {"bg": theme.color4,
                           "width": 200}
style_layersheader = {"bg": theme.color2,
                      "font": theme.titlefont1["type"],
                      "fg": theme.titlefont1["color"],
                      "anchor": "w", "padx": 5}

style_layeritem_normal = {"bg": theme.color4,
                          "width": 200,
                          "relief": "ridge"}
style_layercheck = {"bg": theme.color4}
style_layername_normal = {"bg": theme.color4,
                   "fg": theme.font1["color"],
                   "font": theme.font1["type"],
                   "relief": "flat",
                   "anchor": "w"}

# Import GIS functionality
import pythongis as pg
from . import dispatch

# Panes

class LayerItem(tk.Frame):
    def __init__(self, master, renderlayer, name=None, **kwargs):
        # get theme style
        style = style_layeritem_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **style)
        self.layerspane = self.master.master
        self.statusbar = self.layerspane.statusbar

        # Create a frame to place main row with name etc
        self.firstrow = tk.Frame(self, **style)
        self.firstrow.pack(side="top", fill="x", expand=True)

        # Create the visibility check box
        var = tk.BooleanVar(self)
        self.checkbutton = tk.Checkbutton(self.firstrow, variable=var, offvalue=False, onvalue=True, command=self.toggle_visibility, **style_layercheck)
        self.checkbutton.var = var
        self.checkbutton.pack(side="left")
        self.checkbutton.select()

        # Create Delete button to the right
        self.deletebutton = IconButton(self.firstrow, padx=2, relief="flat", command=self.delete)
        self.deletebutton.set_icon("delete_layer.png")
        self.deletebutton.pack(side="right")

        # Create the layername display
        self.renderlayer = renderlayer
        if name: layername = name
        elif self.renderlayer.data.filepath: 
            layername = os.path.split(self.renderlayer.data.filepath)[-1]
        else: layername = "Unnamed layer"
        self.namelabel = tk.Label(self.firstrow, text=layername, **style_layername_normal)
        self.namelabel.pack(side="left", fill="x", expand=True)

        # Bind drag events

        def start_drag(event):
            self.dragging = event.widget.master.master
            self.config(cursor="exchange")
            
        def stop_drag(event):
            
            # find closest layerindex to release event
            def getindex(layeritem):
                return self.layerspane.layers.get_position(layeritem.renderlayer)
            
            goingdown = event.y_root - (self.dragging.winfo_rooty() + self.dragging.winfo_height() / 2.0) > 0
            if goingdown:
                i = len(self.layerspane.layersview.winfo_children())
                for layeritem in sorted(self.layerspane.layersview.winfo_children(), key=getindex, reverse=True):
                    if event.y_root < layeritem.winfo_rooty() + layeritem.winfo_height() / 2.0:
                        break
                    i -= 1
            else:
                i = 0
                for layeritem in sorted(self.layerspane.layersview.winfo_children(), key=getindex):
                    if event.y_root > layeritem.winfo_rooty() - layeritem.winfo_height() / 2.0:
                        break
                    i += 1
                    
            # move layer
            frompos = self.layerspane.layers.get_position(self.dragging.renderlayer)
            if i != frompos:
                self.layerspane.move_layer(frompos, i)
                
            # clean up
            self.dragging = None
            self.config(cursor="arrow")

        self.dragging = None
        self.namelabel.bind("<Button-1>", start_drag)
        self.namelabel.bind("<ButtonRelease-1>", stop_drag)

        # Bind right click
        #self.namelabel.bind("<Button-3>", self.right_click)

    def toggle_visibility(self):
        self.layerspane.toggle_layer(self)

    def delete(self):
        self.layerspane.remove_layer(self)

    def ask_rename(self):
        # place entry widget on top of namelabel
        nameentry = tk.Entry(self)
        nameentry.place(x=self.namelabel.winfo_x(), y=self.namelabel.winfo_y(), width=self.namelabel.winfo_width(), height=self.namelabel.winfo_height())
        # set its text to layername and select all text
        nameentry.insert(0, self.namelabel["text"])
        nameentry.focus()
        nameentry.selection_range(0, tk.END)
        def finish(event):
            newname = nameentry.get()
            nameentry.destroy()
            self.namelabel["text"] = newname
        def cancel(event):
            nameentry.destroy()
        nameentry.bind("<Return>", finish)
        nameentry.bind("<Escape>", cancel)





class LayersPane(tk.Frame):
    def __init__(self, master, layer_rightclick=None, **kwargs):
        # get theme style
        style = style_layerspane_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **style)
        
        # Make the top header
        self.header = tk.Label(self, text="Layers:", **style_layersheader)
        self.header.pack(side="top", fill="x")

        # Then, the layer list view
        self.layersview = tk.Frame(self, **style)
        self.layersview.pack(side="top", fill="x")
        self.pack_propagate(False) # important, this prevents layeritem names from deciding the size of layerspane

        # FOR TESTING ONLY
        # LOAD EXAMPLE DATA
        def load_testvector(event):
            self.add_layer("test_files/geoj/cshapes.geo.json")
        self.winfo_toplevel().bind("v", load_testvector)
        def load_testraster(event):
            self.add_layer("test_files/geotiff/TrueMarble.16km.2700x1350.tif")
        self.winfo_toplevel().bind("r", load_testraster)

    def __iter__(self):
        for layeritem in self.layersview.winfo_children():
            yield layeritem

    def assign_layergroup(self, layergroup):
        layergroup.layerspane = self
        self.layers = layergroup

    def add_layer(self, filepath_or_loaded, name=None):
        
        def from_filepath(filepath):
            if filepath.lower().endswith((".shp",".geojson",".json")):
                func = pg.GeoTable
                args = (filepath,)
            elif filepath.lower().endswith((".asc",".ascii",
                                            ".tif",".tiff",".geotiff",
                                            ".jpg",".jpeg",
                                            ".png",".bmp",".gif")):
                func = pg.Raster
                args = (filepath,)
            else:
                popup_message(self, "Fileformat not supported\n\n" + filepath )
                return

            self.statusbar.task.start("Loading layer from file...")
            pending = dispatch.request_results(func, args)

            def finish(loaded):
                if isinstance(loaded, Exception):
                    popup_message(self, str(loaded) + "\n\n" + filepath )
                else:
                    from_loaded(loaded)
                self.statusbar.task.stop()
                
            dispatch.after_completion(self, pending, finish)

        def from_loaded(loaded):
            # add the data as a rendering layer
            if isinstance(loaded, pg.GeoTable):
                renderlayer = pg.VectorLayer(loaded)
            elif isinstance(loaded, pg.Raster):
                renderlayer = pg.RasterLayer(loaded)
            self.layers.add_layer(renderlayer)

            # list a visual representation in the layerspane list
            listlayer = LayerItem(self.layersview, renderlayer=renderlayer, name=name)
            listlayer.namelabel.bind("<Button-3>", self.layer_rightclick)
            listlayer.pack(fill="x", side="bottom")
                       
            # render to and update all mapcanvases connected to the layergroup
            for mapcanvas in self.layers.connected_maps:
                func = mapcanvas.render_one
                args = [renderlayer]

                self.statusbar.task.start("Rendering layer...")
                pending = dispatch.request_results(func, args)
                
                def finish(loaded):
                    if isinstance(loaded, Exception):
                        popup_message(self, "Rendering error: " + str(loaded) )
                    else:
                        mapcanvas.mapview.update_image()
                    self.statusbar.task.stop()
                    
                dispatch.after_completion(self, pending, finish)

        # load from file or go straight to listing/rendering
        if isinstance(filepath_or_loaded, (str,unicode)):
            from_filepath(filepath_or_loaded)
        else:
            from_loaded(filepath_or_loaded)

    def toggle_layer(self, layeritem):
        # toggle visibility
        if layeritem.renderlayer.visible == True:
            layeritem.renderlayer.visible = False
        elif layeritem.renderlayer.visible == False:
            layeritem.renderlayer.visible = True
        # update all mapcanvas
        for mapcanvas in self.layers.connected_maps:
            mapcanvas.update_draworder()
            mapcanvas.mapview.update_image()

    def remove_layer(self, layeritem):
        # remove from rendering
        layerpos = self.layers.get_position(layeritem.renderlayer)
        self.layers.remove_layer(layerpos)
        for mapcanvas in self.layers.connected_maps:
            mapcanvas.update_draworder()
            mapcanvas.mapview.update_image()
        # remove from layers list
        layeritem.destroy()

    def move_layer(self, fromindex, toindex):
        self.layers.move_layer(fromindex, toindex)
        for mapcanvas in self.layers.connected_maps:
            mapcanvas.update_draworder()
            mapcanvas.mapview.update_image()
        self.update_layerlist()

    def update_layerlist(self):
        def getindex(layeritem):
            return self.layers.get_position(layeritem.renderlayer)
        for layeritem in sorted(self.layersview.winfo_children(), key=getindex, reverse=True):
            layeritem.pack_forget()
            layeritem.pack(fill="x")

    def bind_layer_rightclick(self, func):
        self.layer_rightclick = func

    def assign_statusbar(self, statusbar):
        self.statusbar = statusbar
            
