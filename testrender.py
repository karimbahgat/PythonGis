import pythongis as pg


###
print("\n"+"point test")
vect = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\shp\domestic.shp")
print vect.fields

vect.view(1000,500,
            fillsize={"breaks":"headtail",
                        "key":lambda f: float(f["Average_nk"]),
                        "fromval":0.2,
                        "toval":2},
            fillcolor={"breaks":"headtail",
                        "key":lambda f: float(f["Average_nk"]),
                        "fromval":(0,255,255,255),
                        "toval":(255,0,0,200)},
            sortkey=lambda f: float(f["Average_nk"]),
            sortorder="decr"
            )


###
print("\n"+"polygon test")
vect = pg.vector.data.VectorData(r"C:\Users\kimo\Documents\GitHub\pShapes\BaseData\ne_10m_admin_1_states_provinces.shp",
                                 encoding="latin")
print(vect.fields)
vect.view(1000,500,
            fillcolor={"breaks":"quantile",
                        "key":lambda f: float(f["latitude"]),
                        "fromval":(0,255,255),
                        "toval":(255,0,0)}
            )

###
print("\n"+"unique categories test")
vect.view(1000,500,
            fillcolor={"breaks":"unique",
                        "key":lambda f: float(f["latitude"]),
                        "fromval":None,
                        "toval":None,
                       "classvalues":["red","blue","yellow","green","orange"]}
            )
