
import pythongis as pg

data = pg.VectorData(r"C:\Users\kimok\Downloads\cshapes\cshapes.shp")
#data = pg.VectorData(r"C:\Users\karbah\Dropbox\PRIO\2016, CShapes\cshapes.shp")

m = data.map(4000,2000)
m.add_layer(data)
m.title = "Test title"
m.add_legend({'direction':'s'})
leg = m.foregroundgroup[-1]
leg.add_single_symbol(m.layers[0], title="Extra")
m.view()

fdsf




##mapp = pg.renderer.Map(background="blue")
##mapp.add_layer(data,
##               text=lambda f: f["CNTRY_NAME"],
##               textoptions=dict(textsize=6))
##
##import tk2
##win = tk2.Tk()
##
##mapview = pg.app.map.MapView(win, mapp)
##mapview.pack(fill="both", expand=1)
##
##layerscontrol = pg.app.controls.LayersControl(mapview)
##layerscontrol.place(relx=0.98, rely=0.02, anchor="ne")
##mapview.add_control(layerscontrol)
##
##navigcontrol = pg.app.controls.NavigateControl(mapview)
##navigcontrol.place(relx=0.5, rely=0.02, anchor="n")
##mapview.add_control(navigcontrol)
##
##zoomcontrol = pg.app.controls.ZoomControl(mapview)
##zoomcontrol.place(relx=0.02, rely=0.02, anchor="nw")
##mapview.add_control(zoomcontrol)
##
##progbar = tk2.progbar.NativeProgressbar(win)
##progbar.pack()
##
##def startprog():
##    progbar.start()
##def stopprog():
##    progbar.stop()
##mapview.onstart = startprog
##mapview.onfinish = stopprog
##
##win.mainloop()
