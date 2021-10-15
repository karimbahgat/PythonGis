
import pythongis as pg



# overlap

group = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_convexes.shp")
values = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_centroids.shp")

print group.fields
print values.fields

summ = pg.vector.analyzer.overlap_summary(group, values, fieldmapping=[("countagg",lambda f: f["GWEYEAR"],"count")])
print summ
for f in summ:
    print f.row[-1]
summ.view(1000,500,
          fillcolor={"breaks": "natural",
                     "key": lambda f: f["countagg"],
                     "valuestops": [(255,0,0),(255,255,0),(0,255,0)]
                     }
          )



# within distance

group = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_convexes.shp")
values = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_centroids.shp")

print group.fields
print values.fields

summ = pg.vector.analyzer.near_summary(group, values, radius=1.5, n=10,
                                        fieldmapping=[("countagg",lambda f: f["GWEYEAR"],"count")])
print summ
for f in summ:
    print f.row[-1]
summ.view(1000,500,
          fillcolor={"breaks": "natural",
                     "key": lambda f: f["countagg"],
                     "valuestops": [(255,0,0),(255,255,0),(0,255,0)]
                     }
          )
