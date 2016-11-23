
from .map import MapView



##def view_data(data, width=None, height=None, bbox=None, flipy=True, **styleoptions):
##    mapp = data.render(width, height, bbox, flipy, **styleoptions)
##    
##    import tk2
##    
##    win = tk2.Tk()
##
##    mapview = MapView(win, mapp)
##    mapview.pack(fill="both", expand=1)
##    
##    return win




import pythongis as pg
import tk2

class MiniGUI(tk2.basics.Label):
    def __init__(self, master, mapp, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        mapview = pg.app.map.MapView(self, mapp)
        mapview.pack(fill="both", expand=1)

        layerscontrol = pg.app.controls.LayersControl(mapview)
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

