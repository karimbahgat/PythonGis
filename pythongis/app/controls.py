
import os
import tk2

import pythongis as pg
from . import dialogs
from . import builder
from . import icons


class LayersControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.layersbut = tk2.basics.Button(self)
        self.layersbut["command"] = self.toggle_layers
        self.layersbut.set_icon(icons.iconpath("layers.png"), width=40, height=40)
        self.layersbut.pack()

        self.layers = []

        w = self
        while w.master:
            w = w.master
        self._root = w
        self.layerslist = tk2.scrollwidgets.OrderedList(self._root)

    def toggle_layers(self):
        if self.layerslist.winfo_ismapped():
            self.hide_layers()
        else:
            self.show_layers()

    def show_layers(self):
        for w in self.layerslist.items:
            w.destroy()
        for lyr in self.layers:
            self.layerslist.add_item(lyr, self.layer_decor)
            
        def add_layer():
            # TODO: maybe open another dialogue where can set encoding, filtering, etc, before adding
            filepath = tk2.filedialog.askopenfilename()
            datawin = dialogs.LoadDataDialog(filepath=filepath)
            def onsuccess(data):
                # TODO: should prob be threaded...
                lyr = self.mapview.renderer.add_layer(data)
                self.show_layers()
                self.mapview.renderer.render_one(lyr)
                self.mapview.renderer.update_draworder()
                self.mapview.update_image()
            datawin.onsuccess = onsuccess
        def buttondecor(w):
            but = tk2.Button(w, text="Add Layer", command=add_layer)
            but.pack()
        self.layerslist.add_item(None, buttondecor)
        
        screenx,screeny = self.layersbut.winfo_rootx(),self.layersbut.winfo_rooty()
        x,y = screenx - self._root.winfo_rootx(), screeny - self._root.winfo_rooty()
        self.layerslist.place(anchor="ne", x=x, y=y)

    def hide_layers(self):
        self.layerslist.place_forget()

    def layer_decor(self, widget):
        """
        Default way to decorate each layer with extra widgets
        Override method to customize. 
        """
        widget.pack(fill="x", expand=1)
        
        visib = tk2.basics.Checkbutton(widget)
        visib.select()
        def toggle():
            lyr = widget.item
            lyr.visible = not lyr.visible
            if lyr.visible:
                self.mapview.renderer.render_one(lyr)
            self.mapview.renderer.update_draworder()
            self.mapview.update_image()
        visib["command"] = toggle
        visib.pack(side="left")
        
        text = widget.item.data.name
        if len(text) > 50:
            text = "..."+text[-47:]
        name = tk2.basics.Label(widget, text=text)
        name.pack(side="left", fill="x", expand=1)
        
        def browse():
            from . import builder
            win = tk2.Window()
            win.state('zoom')
            browser = builder.TableBrowser(win)
            browser.pack(fill="both", expand=1)
            lyr = widget.item
            fields = lyr.data.fields
            rows = (feat.row for feat in lyr.features()) # respects the filter
            browser.table.populate(fields, rows)
            
        browse = tk2.basics.Button(widget, text="Browse", command=browse)
        browse.pack(side="right")

    def move_layer(self):
        pass

class NavigateControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.zoomglob = tk2.basics.Button(self)
        self.zoomglob["command"] = lambda: self.mapview.zoom_global()
        self.zoomglob.set_icon(icons.iconpath("zoom_global.png"), width=40, height=40)
        self.zoomglob.pack(side="left")

        self.zoomrect = tk2.basics.Button(self)
        self.zoomrect["command"] = lambda: self.mapview.zoom_rect()
        self.zoomrect.set_icon(icons.iconpath("zoom_rect.png"), width=40, height=40)
        self.zoomrect.pack(side="left")

class ZoomControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.zoomin = tk2.basics.Button(self)
        self.zoomin["command"] = lambda: self.mapview.zoom_in()
        self.zoomin["text"] = "+"
        self.zoomin.pack()

        self.zoomout = tk2.basics.Button(self)
        self.zoomout["command"] = lambda: self.mapview.zoom_out()
        self.zoomout["text"] = "-"
        self.zoomout.pack()

class IdentifyControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.identifybut = tk2.basics.Button(self, command=self.begin_identify)
        self.identifybut.set_icon(icons.iconpath("identify.png"), width=40, height=40)
        self.identifybut.pack()

        self.mouseicon_tk = icons.get("identify.png", width=30, height=30)

    def begin_identify(self):
        print "begin identify..."
        # replace mouse with identicon
        self.mouseicon_on_canvas = self.mapview.create_image(-100, -100, anchor="nw", image=self.mouseicon_tk )
        #self.mapview.config(cursor="none")
        def follow_mouse(event):
            # gets called for entire app, so check to see if directly on canvas widget
            root = self.winfo_toplevel()
            rootxy = root.winfo_pointerxy()
            mousewidget = root.winfo_containing(*rootxy)
            if mousewidget == self.mapview:
                curx,cury = self.mapview.canvasx(event.x), self.mapview.canvasy(event.y)
                self.mapview.coords(self.mouseicon_on_canvas, curx, cury)
        self.followbind = self.winfo_toplevel().bind('<Motion>', follow_mouse, '+')
        # identify once clicked
        def callident(event):
            # reset
            cancel()
            # find
            x,y = self.mapview.mouse2coords(event.x, event.y)
            self.identify(x, y)
        self.clickbind = self.winfo_toplevel().bind("<ButtonRelease-1>", callident, "+")
        # cancel with esc button
        def cancel(event=None):
            self.winfo_toplevel().unbind('<Motion>', self.followbind)
            self.winfo_toplevel().unbind('<ButtonRelease-1>', self.clickbind)
            self.winfo_toplevel().unbind('<Escape>', self.cancelbind)
            #self.mapview.config(cursor="arrow")
            self.mapview.delete(self.mouseicon_on_canvas)
        self.cancelbind = self.winfo_toplevel().bind("<Escape>", cancel, "+")

    def identify(self, x, y):
        print "identify: ",x, y
        infowin = tk2.Window()
        infowin.state('zoomed')

        title = tk2.Label(infowin, text="Hits for coordinates: %s, %s" % (x, y))
        title.pack(fill="x")#, expand=1)
        
        infoframe = tk2.Frame(infowin)
        infoframe.pack(fill="both", expand=1)

        # find coord distance for approx 5 pixel uncertainty
        pixelbuff = 10
        p1 = self.mapview.renderer.pixel2coord(0, 0)
        p2 = self.mapview.renderer.pixel2coord(pixelbuff, 0)
        coorddist = self.mapview.renderer.drawer.measure_dist(p1, p2)

        # create uncertainty buffer around clickpoint
        from shapely.geometry import Point
        p = Point(x, y).buffer(coorddist)
        
        anyhits = None
        for layer in self.mapview.renderer.layers:
            print layer
            if isinstance(layer.data, pg.VectorData):                
                feats = [feat for feat in layer.data.quick_overlap(p.bounds) if feat.get_shapely().intersects(p)]
                
                if feats:
                    anyhits = True
                    layerframe = tk2.Frame(infoframe, label=layer.data.name)
                    layerframe.pack(fill="both", expand=1)
                    
                    browser = builder.TableBrowser(layerframe)
                    browser.pack(fill="both", expand=1)
                    browser.table.populate(fields=layer.data.fields, rows=[f.row for f in feats])
                    
            elif isinstance(layer.data, pg.RasterData):
                values = [layer.data.get(x, y, band).value for band in layer.data.bands]
                if any(values):
                    anyhits = True
                    layerframe = tk2.Frame(infoframe, label=layer.data.name)
                    layerframe.pack(fill="both", expand=1)
                    
                    col,row = layer.data.geo_to_cell(x, y)
                    cellcol = tk2.Label(layerframe, text="Column: %s" % col )
                    cellcol.pack(fill="x", expand=1)
                    cellrow = tk2.Label(layerframe, text="Row: %s" % row )
                    cellrow.pack(fill="x", expand=1)

                    for bandnum,val in enumerate(values):
                        text = "Band %i: \n\t%s" % (bandnum, val)
                        valuelabel = tk2.Label(layerframe, text=text)
                        valuelabel.pack(fill="both", expand=1)

        if not anyhits:
            infowin.destroy()

class TimeControl(tk2.basics.Label):
    def __init__(self, master, key=None, start=None, end=None, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.slider = tk2.Slider(self)
        self.slider.pack(fill="both", expand=1)

##    def gg
##        for lyr in self.mapview.layers:
##            alldates = key(f) for f in self.mapview.la
##
##        if not start:
##            start = min(

class InsetMapControl:
    def __init__(self, master, *args, **kwargs):
        pass




