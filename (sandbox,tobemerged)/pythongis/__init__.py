
from . import vector
from . import raster
from . import renderer
from . import app



# consider cutting out below for the sake of separated namespaces...
# instead just create certain toplevel convenience functions that are
# raster/vector ignorant, eg pg.load()
from .vector.data import *
from .vector.manager import *
from .raster.data import *
#from .raster.manager import *
from .renderer import *
