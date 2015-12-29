import pythongis as pg


###
print("\n"+"canvas test")
mapp = pg.renderer.MapCanvas(1000, 500)

rast = pg.raster.data.RasterData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\geotiff\TrueMarble.16km.2700x1350.tif")
mapp.layers.add_layer(pg.renderer.RasterLayer(rast))

vect = pg.vector.data.VectorData(r"C:\Users\kimo\Documents\GitHub\pShapes\BaseData\ne_10m_admin_1_states_provinces.shp", encoding="latin")
mapp.layers.add_layer(pg.renderer.VectorLayer(vect,
                                                fillcolor={"breaks":"equal",
                                                            "key":lambda f: float(f["latitude"]),
                                                            "valuestops":[(0,255,255,255),(255,255,0,255),(255,0,0,200)],
                                                            "classes":15,
                                                           },
                                              ))

vect = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\shp\domestic.shp")
mapp.layers.add_layer(pg.renderer.VectorLayer(vect,
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
                                              ))

mapp.zoom_factor(4)

mapp.render_all()
mapp.img.show()

fsdfsdf


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


