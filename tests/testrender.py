import pythongis as pg


# ADD LAYER TRANSPARENCY
# MAP IS ONLY FOR THE MAP, NO PADDING, BC BACKGROUND COLOR FILLS ENTIRE THING
# FIGURE OUT LAYOUT ROLE, THIS IS WHERE YOU CAN HAVE PADDING, TITLE, AND LEGEND. MAP CAN HAVE PADDING ATTRIBUTE, WHICH LAYOUT USES TO PAD AFTER RENDERING.
# ALLOW GIVING CLASSIFIER SIZES IN MISC UNITS
# ADD PROPORTIONAL CLASSIFICATION, USING REAL PROPORTIONAL DIFFERENCES WITHOUT ANY CLASS GROUPINGS, ONLY MAX VS MIN


###
print("\n"+"canvas layers test")
mapp = pg.renderer.Map(background="blue")

#rast = pg.raster.data.RasterData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\geotiff\TrueMarble.16km.2700x1350.tif")
#mapp.layers.add_layer(pg.renderer.RasterLayer(rast))

vect = pg.vector.data.VectorData(r"C:\Users\kimo\Documents\GitHub\pShapes\BaseData\ne_10m_admin_1_states_provinces.shp", encoding="latin")
mapp.add_layer(pg.renderer.VectorLayer(vect, legendoptions=dict(title="Provinces"), 
                                                fillcolor={"breaks":"equal",
                                                            "key":lambda f: float(f["latitude"]),
                                                            "symbolvalues":[(0,255,255,255),(255,255,0,255),(255,0,0,200)],
                                                            "classes":5,
                                                           },
                                              ))

vect = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\shp\domestic.shp")
mapp.add_layer(pg.renderer.VectorLayer(vect, title="Terrorism",
                                                fillsize=1,
                                                           #{"breaks":"natural",
                                                            #"key":lambda f: float(f["Average_nk"]),
                                                            #"symbolvalues":[0.2, 2.0]
                                                            #},
                                                fillcolor="red",
                                                          #{"breaks":"natural",
                                                          #  "key":lambda f: float(f["Average_nk"]),
                                                          #  "symbolvalues":[(0,255,0,255),(255,255,0,255),(255,0,0,255)],
                                                          # },
                                                sortkey=lambda f: float(f["Average_nk"]),
                                                sortorder="incr",
                                              ))

mapp.zoom_bbox(-10,-40,10,40)
#mapp.zoom_in(4)
mapp.view()

#lay = pg.renderer.Layout(1000, 500, title="Layout")
#lay.add_map(mapp)
#lay.add_legend(legendoptions=dict(padding=0), xy=(0,500),anchor="sw")

#lay.view()


fdsfjsdflk


###
print("\n"+"raster test")
rast = pg.raster.data.RasterData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\geotiff\TrueMarble.16km.2700x1350.tif")
rast.view(1000,500, type="colorscale", gradcolors=[(0,0,255),(0,255,0),(255,0,0)])


###
print("\n"+"point test")
vect = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\shp\domestic.shp")
print vect.fields

vect.view(1000,500,
            fillsize={"breaks":"headtail",
                        "key":lambda f: float(f["Average_nk"]),
                        "valuestops":[0.2, 2.0]
                      },
            fillcolor={"breaks":"headtail",
                        "key":lambda f: float(f["Average_nk"]),
                        "valuestops":[(0,255,0,255),(255,255,0,255),(255,0,0,255)],
                       },
            sortkey=lambda f: float(f["Average_nk"]),
            sortorder="incr"
            )


###
print("\n"+"polygon test")
vect = pg.vector.data.VectorData(r"C:\Users\kimo\Documents\GitHub\pShapes\BaseData\ne_10m_admin_1_states_provinces.shp",
                                 encoding="latin")
print(vect.fields)
vect.view(1000,500,
            fillcolor={"breaks":"equal",
                        "key":lambda f: float(f["latitude"]),
                        "valuestops":[(0,255,255,255),(255,255,0,255),(255,0,0,200)],
                        "classes":15,
                       },
            )


###
print("\n"+"unique categories test")
vect.view(1000,500,
            fillcolor={"breaks":"unique",
                        "key":lambda f: float(f["latitude"]),
                        "valuestops":["red","blue","yellow","green","orange"]}
            )


