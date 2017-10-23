
import pythongis as pg

c = pg.VectorData("ch est/data/cshapes.shp")

mapp = pg.renderer.Map(2000,1000)
mapp.add_layer(c,
               fillcolor=dict(breaks="proportional", key="GWCODE"),
               legendoptions=dict(title="Fill color",
                                  #direction="n",
                                  #titleoptions=dict(textsize=38)
                                  ))
mapp.add_legend(legendoptions=dict(#title="Many countries",
                                   ))#titleoptions=dict(textsize="4%w")))
mapp.view()
