
from .map import MapView

import pythongis as pg
import tk2

class MultiLayerGUI(tk2.Tk):
    def __init__(self, mapp, *args, **kwargs):
        tk2.basics.Tk.__init__(self, *args, **kwargs)

        self.map = MultiLayerMap(self, mapp)
        self.map.pack(fill="both", expand=1)

class MultiLayerMap(tk2.basics.Label):
    def __init__(self, master, mapp, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        mapview = pg.app.map.MapView(self, mapp)
        mapview.pack(fill="both", expand=1)

        layerscontrol = pg.app.controls.LayersControl(mapview)
        layerscontrol.layers = mapp.layers
        layerscontrol.place(relx=0.98, rely=0.02, anchor="ne")
        mapview.add_control(layerscontrol)

        navigcontrol = pg.app.controls.NavigateControl(mapview)
        navigcontrol.place(relx=0.5, rely=0.02, anchor="n")
        mapview.add_control(navigcontrol)

        zoomcontrol = pg.app.controls.ZoomControl(mapview)
        zoomcontrol.place(relx=0.02, rely=0.02, anchor="nw")
        mapview.add_control(zoomcontrol)

        progbar = tk2.progbar.NativeProgressbar(self)
        progbar.pack()

        def startprog():
            progbar.start()
        def stopprog():
            progbar.stop()
        mapview.onstart = startprog
        mapview.onfinish = stopprog

class TableBrowser(tk2.basics.Window):
    def __init__(self, *args, **kwargs):
        tk2.basics.Window.__init__(self, *args, **kwargs)

        self.table = tk2.scrollwidgets.Table(self)
        self.table.pack(fill="both", expand=1)

        



