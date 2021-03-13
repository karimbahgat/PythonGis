
import pythongis as pg

data = pg.VectorData(r"C:\Users\kimok\Downloads\cshapes\cshapes.shp")
#data = pg.VectorData(r"C:\Users\karbah\Dropbox\PRIO\2016, CShapes\cshapes.shp")
#data.browse(limit=10)

m = pg.renderer.Map(4000,2000)
m.add_layer(data) # removing this creates error
m.add_layer(r"C:\Users\kimok\Downloads\GRAY_50M_SR_OB\GRAY_50M_SR_OB.tif",
            type='colorscale', gradcolors=['blue','white'])
m.add_layer(data)#.convert.to_points(), fillsize={'key':'AREA'})
m.title = "Test title"
# legend
leg = m.add_legend({'title':'Main legend','direction':'s'})
leg.add_single_symbol(m.layers[0], title="Custom symbol")
# legend 2
leg = pg.renderer.Legend(title="Legend 2")
leg.add_single_symbol(m.layers[0], title="Custom symbol")
m.add_legend(leg, xy=('99%w','99%h'), anchor='se')
#
#m.render()
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
