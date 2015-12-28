
import pythongis as pg

# sql test
##conv = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_convexes.shp")
##conv.view(1000,500)
##print conv.fields
##
##import shapely,shapely.ops
##iterable = ((feat,feat.get_shapely()) for feat in conv)
##q = pg.vector.sql.query(_from=[iterable],
##                         _groupby=lambda ((f,g),): f["CNTRY_NAME"][0] < "N",
##                         #_where=lambda (f,g): f["GWSYEAR"]>1946,
##                         _select=[("avgendyr",
##                                   lambda ((f,g),): f["GWEYEAR"],
##                                   "average")],
##                         _geomselect=lambda (items,): shapely.ops.cascaded_union([geom for feat,geom in items]).__geo_interface__,
##                        #_limit=9
##                        )
##buf = pg.vector.sql.query_to_data(q)
##buf.view(1000,500)
##
##gfdgfdgdfgd
##



# clip test
conv = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_convexes.shp")
tess = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_triangles.shp")

conv.view(1000,500)
tess.view(1000,500)

res = pg.vector.analyzer.clip(conv, tess)
print res
res.view(1000,500)



# dissolve test
conv = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_convexes.shp")
conv.view(1000,500)
print conv.fields

key = lambda combi: combi[0][0]["CNTRY_NAME"][0] # first char of country
fieldmapping = [("avgendyr", lambda combi: combi[0][0]["GWEYEAR"], "average"),
                ("key",key,"first")]

res = pg.vector.analyzer.glue(conv, key=key, fieldmapping=fieldmapping, contig=False)
res.view(1000,500)

fdsfas



# cut test
conv = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_convexes.shp")
tess = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_triangles.shp")

conv.view(1000,500)
tess.view(1000,500)

res = pg.vector.analyzer.cut(conv, tess)
print res
res.view(1000,500)
