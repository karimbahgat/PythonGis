
import pythongis as pg

dat = pg.VectorData(r"C:\Users\karbah\Dropbox\PRIO\Misc\priocountries\priocountries.shp")

# sizes

mapp = pg.renderer.Map()
mapp.add_layer(dat, fillcolor="yellow", nolegend=True)
mapp.add_layer(dat.convert.to_points(),
               fillsize=dict(breaks="natural",
                             key="POP_EST",
                             sizes=[0.5, 2.0],
                             exclude=[-99]),
               outlinewidth=0.4,
               legendoptions=dict(title="Population",
                                  titleoptions=dict(textsize=14),#, font="Segoe UI"),
                                  labeloptions=dict(textsize=12),#, font="Segoe UI"),
                                  valueformat=",.0f")
               )
mapp.add_legend()
mapp.view()

mapp = pg.renderer.Map()
mapp.add_layer(dat, fillcolor="yellow", nolegend=True)
mapp.add_layer(dat.convert.to_points(),
               fillsize=dict(breaks="proportional",
                                           key="POP_EST",
                                           sizes=[0.5, 5.0],
                                           exclude=[-99]),
               outlinewidth=0.4,
               legendoptions=dict(title="Population",
                                  titleoptions=dict(textsize=14),#, font="Segoe UI"),
                                  labeloptions=dict(textsize=12),#, font="Segoe UI"),
                                  valueformat=",.0f")
               )
mapp.add_legend()
mapp.view()

# colors

##mapp = pg.renderer.Map()
##mapp.add_layer(dat,
##               fillcolor=dict(breaks="natural",
##                                           key="POP_EST",
##                                           colors=["green","yellow","red"]),
##               outlinewidth=0.2,
##               legendoptions=dict(title="Population",
##                                  titleoptions=dict(textsize=14),#, font="Segoe UI"),
##                                  labeloptions=dict(textsize=12),#, font="Segoe UI"),
##                                  valueformat=",.0f")
##               )
##mapp.add_legend()
##mapp.view()
##
##mapp = pg.renderer.Map()
##mapp.add_layer(dat,
##               fillcolor=dict(breaks="proportional",
##                                           key="POP_EST",
##                                           colors=["green","yellow","red"]),
##               outlinewidth=0.2,
##               legendoptions=dict(title="Population",
##                                  titleoptions=dict(textsize=14),#, font="Segoe UI"),
##                                  labeloptions=dict(textsize=12),#, font="Segoe UI"),
##                                  valueformat=",.0f")
##               )
##mapp.add_legend()
##mapp.view()

