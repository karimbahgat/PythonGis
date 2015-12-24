
import pythongis as pg



# overlap

group = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_convexes.shp")
values = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_centroids.shp")

print group.fields
print values.fields

summ = pg.vector.analyzer.overlap_summary(group, values, fieldmapping=[("GWEYEAR","count")])
print summ
for f in summ:
    print f.row[-1]



# within distance

group = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_lines.shp")
values = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_centroids.shp")

print group.fields
print values.fields

summ = pg.vector.analyzer.near_summary(group, values, radius=1.5, n=10,
                                           fieldmapping=[("GWEYEAR","count")])
print summ
for f in summ:
    print f.row[-1]
