# Import system modules
import sys, time

# Import GUI modules
from Tkinter import *
from tkFileDialog import askopenfilenames

# Import python gis module
scriptspace = r"C:\Users\BIGKIMO\Dropbox\Work\Research\Software\Various Python Libraries\custommodules"
sys.path.append(scriptspace)
import mapengine as pygis

# CUSTOMIZING
mapwidth = 1000
mapheight = 500
mainbgcolor = "burlywood3"
bottominfobgcolor = "black"
bottominfotxtcolor = "white"

# INITIATE GUI
window = Tk()
window.wm_title("Python GIS")
window.state('zoomed')
window_colored = Frame(master=window, bg=mainbgcolor)
window_colored.pack(fill="both", expand=True)

# FIRST, CREATE AREA WHERE MAP WILL BE PLACED
maparea = Frame(master=window, bg=mainbgcolor)
maparea.place(relx=0.03, rely=0.06, relwidth=0.96, relheight=0.93)
# EMBED MAP TO THE WIDGET AREA CREATED ABOVE
MAPWIDGET = pygis.MapWidget(parentwidget=maparea, mapdimensions=(mapwidth,mapheight), numpyspeed=False)



# FINALLY, CREATE TOP BUTTON AREA WITH BUTTONS
buttonarea = Frame(master=window, bg=mainbgcolor)
buttonarea.place(relx=0.03, rely=0.01, relwidth=0.96, relheight=0.04)
# BUTTON: ADD SHAPEFILE
def selectfile():
    userchoice = askopenfilenames(filetypes=[("shapefiles",".shp")])
    userchoice = [ each.replace("{","").replace("}","") for each in userchoice.split("} {") ]
    print userchoice
    MAPWIDGET.LoadShapefiles(inputshapefilepaths=userchoice)
button_addshapefile = Button(master=MAPWIDGET.map.layersframe_header, text="+", bg="yellow", command=selectfile)
button_addshapefile.pack(side="right", anchor="e", ipadx=3, padx=6)
button_fullextent = Button(master=buttonarea, text="O", bg="dark grey", command=MAPWIDGET.map.FullExtent)
button_fullextent.pack(side="left", ipadx=3)
MAPWIDGET.map.bottominfo.config(bg=bottominfobgcolor, fg=bottominfotxtcolor)
MAPWIDGET.map.coordsdisplay.config(bg=bottominfobgcolor, fg=bottominfotxtcolor)
MAPWIDGET.map.zoomdisplay.config(bg=bottominfobgcolor, fg=bottominfotxtcolor)
MAPWIDGET.map.projectiondisplay.config(bg=bottominfobgcolor, fg=bottominfotxtcolor)

# RUN
window.mainloop()
