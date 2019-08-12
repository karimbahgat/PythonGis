
import pythongis as pg

rw = 6
rh = 3
w = 360
h = 180
xscale = w/float(rw)
yscale = h/float(rh)
affine = [xscale,0,-180,
          0,-yscale,90]
r = pg.RasterData(width=rw, height=rh, mode='float32', affine=affine)
rb = r.add_band()
for y in range(rh):
    for x in range(rw):
        rb.set(x, y, (x+1)*(y+1))

v = pg.VectorData()
bounds = [(-180,-90),(180,-90),(180,90),(-180,90)]
bounds.append(bounds[0])
v.add_feature([],
              {'type':'Polygon',
               'coordinates':[bounds]}
              )

m = pg.renderer.Map(2000,1000,'white')
m.add_layer(r)
m.add_layer(v, fillcolor=None, outlinecolor='red')
m.zoom_auto()
m.view()
