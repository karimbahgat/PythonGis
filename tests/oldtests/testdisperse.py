
import pythongis as pg

v = pg.VectorData("C:/Users/karbah/Dropbox/PRIO/Misc/priocountries/priocountries.shp")

r = pg.raster.analyzer.disperse(v,
                                valuekey=lambda f: f["POP_EST"],
                                bbox=[-180,90,180,-90],
                                width=720, height=360)

r.view()
