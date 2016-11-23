
import os
import tk2

def iconpath(name):
    return os.path.join(os.path.dirname(__file__), "icons", name)

class LayersControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.layersbut = tk2.basics.Button(self)
        self.layersbut.set_icon(iconpath("layers.png"), width=40, height=40)
        self.layersbut.pack()

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

