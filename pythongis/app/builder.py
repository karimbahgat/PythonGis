
from .map import MapView

import pythongis as pg
import tk2

class TableGUI(tk2.Tk):
    def __init__(self, *args, **kwargs):
        tk2.basics.Tk.__init__(self, *args, **kwargs)

        self.browser = TableBrowser(self)
        self.browser.pack(fill="both", expand=1)

        self.state('zoomed')
        

class MultiLayerGUI(tk2.Tk):
    def __init__(self, mapp, time=False, *args, **kwargs):
        tk2.basics.Tk.__init__(self, *args, **kwargs)

        self.map = MultiLayerMap(self, mapp, time=time)
        self.map.pack(fill="both", expand=1)

        self.state('zoomed')

# move below to "widgets.py"..?

class MultiLayerMap(tk2.basics.Label):
    def __init__(self, master, mapp, time=False, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        mapview = pg.app.map.MapView(self, mapp)
        mapview.pack(fill="both", expand=1)

        layerscontrol = pg.app.controls.LayersControl(mapview)
        layerscontrol.layers = mapp.layers
        layerscontrol.place(relx=0.98, rely=0.02, anchor="ne")
        mapview.add_control(layerscontrol)

        identcontrol = pg.app.controls.IdentifyControl(mapview)
        identcontrol.place(relx=0.98, rely=0.98, anchor="se")
        mapview.add_control(identcontrol)

        navigcontrol = pg.app.controls.NavigateControl(mapview)
        navigcontrol.place(relx=0.5, rely=0.02, anchor="n")
        mapview.add_control(navigcontrol)

        zoomcontrol = pg.app.controls.ZoomControl(mapview)
        zoomcontrol.place(relx=0.02, rely=0.02, anchor="nw")
        mapview.add_control(zoomcontrol)

        #bottom = tk2.Label(self)
        #bottom.pack(fill="x", expand=1)
        
        progbar = tk2.progbar.NativeProgressbar(self)
        progbar.pack(side="left", padx=4, pady=4)

        def startprog():
            progbar.start()
        def stopprog():
            progbar.stop()
        mapview.onstart = startprog
        mapview.onfinish = stopprog

        coords = tk2.Label(self)
        coords.pack(side="right", padx=4, pady=4)

        def showcoords(event):
            x,y = mapview.mouse2coords(event.x, event.y)
            coords["text"] = "%s, %s" % (x,y)
        self.winfo_toplevel().bind("<Motion>", showcoords, "+")

        if True:#time:
            # must be dict
            timecontrol = pg.app.controls.TimeControl(mapview)#, **time)
            timecontrol.place(relx=0.5, rely=0.98, anchor="s")
            mapview.add_control(timecontrol)

class TableBrowser(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.table = tk2.scrollwidgets.Table(self)
        self.table.pack(fill="both", expand=1)

        



