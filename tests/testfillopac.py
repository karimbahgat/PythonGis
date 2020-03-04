
import pythongis as pg

data = pg.VectorData('data/ne_10m_admin_0_countries.shp')

data.view(fillcolor='green', fillopacity={'key':'POP_EST', 'opacities':[0.3,1.0]})

##data.view(fillcolor={'key':'POP_EST', 'colors':['beige','red']},
##          fillopacity={'key':lambda f: f.get_shapely().area, 'opacities':[1.0,0.3]},
##          )



