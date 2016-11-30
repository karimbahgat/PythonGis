
import os
import tk2

def iconpath(name):
    return os.path.join(os.path.dirname(__file__), "icons", name)

class LayersControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.layersbut = tk2.basics.Button(self)
        self.layersbut["command"] = self.toggle_layers
        self.layersbut.set_icon(iconpath("layers.png"), width=40, height=40)
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
        text = widget.item.data.name
        if len(text) > 50:
            text = text[47]+"..."
        name = tk2.basics.Label(widget, text=text)
        name.pack(side="left", fill="x", expand=1)
        
        def browse():
            from . import builder
            win = tk2.Window()
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
        self.zoomglob.set_icon(iconpath("zoom_global.png"), width=40, height=40)
        self.zoomglob.pack(side="left")

        self.zoomrect = tk2.basics.Button(self)
        self.zoomrect["command"] = lambda: self.mapview.zoom_rect()
        self.zoomrect.set_icon(iconpath("zoom_rect.png"), width=40, height=40)
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

        self.identifybut = tk2.basics.Button(self)
        #self.identifybut.set_icon(iconpath("layers.png"), width=40, height=40)
        self.identifybut["text"] = "?"
        self.identifybut.pack()

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






