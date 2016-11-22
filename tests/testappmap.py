
import pythongis as pg

data = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.5-1\cshapes.shp")
mapp = pg.renderer.Map(background="blue")
mapp.add_layer(data,
               text=lambda f: f["CNTRY_NAME"],
               textoptions=dict(textsize=4))

import tk2
win = tk2.Tk()

mapview = pg.app.map.MapView(win, mapp)
mapview.pack(fill="both", expand=1)

win.mainloop()
