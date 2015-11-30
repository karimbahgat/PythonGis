
# Import builtins
import sys, os

# Import GUI library
import Tkinter as tk
from tkFileDialog import askopenfilenames


# The Ribbon/Tab system

class Ribbon(tk.Frame):
    """
    Can switch between a series of logically grouped toolbar areas (tabs).
    """
    current_color = "green"
    inactive_color = "pink"
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, parentwidget, height=120)
        self.tabs_area = tk.Frame(self, height=30, bg=self.inactive_color)
        self.tabs_area.pack(fill="x", side="top")
        self.toolbars_area = tk.Frame(self, height=90, bg=self.current_color)
        self.toolbars_area.pack(fill="x", side="top")
        # Populate with tabs
        self.tabs = dict()
        hometab = HomeTab(self.toolbars_area, bg=self.current_color)
        self.add_tab(hometab)
        overlaytab = OverlayTab(self.toolbars_area, bg=self.current_color)
        self.add_tab(overlaytab)
        self.switch(event=None, tabname="Home")

    def add_tab(self, tab):
        self.tabs[tab.name] = tab
        self.current = tab
        # add tab to tabs area
        tab.selector = tk.Label(self.tabs_area, text=tab.name, padx=10, pady=5)
        tab.selector.pack(side="left", padx=5)
        # add tab to toolbars area
        tab.place(relwidth=1, relheight=1)
        # make tab selector selectable
        tab.selector.bind("<Button-1>", self.switch)

    def switch(self, event=None, tabname=None):
        if event: tabname = event.widget["text"]
        # deactivate old tab
        self.current.selector["bg"] = self.inactive_color
        # activate new tab
        self.current = self.tabs[tabname]
        self.current.selector["bg"] = self.current_color
        self.current.lift()

class HomeTab(tk.Frame):
    """
    An area containing general toolbars.
    """
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, parentwidget, **kwargs)
        self.name = "Home"
        self.selection = SelectionTB(self)
        self.selection.pack(side="left", padx=10, pady=10)

class OverlayTab(tk.Frame):
    """
    An area containing overlay analysis toolbars.
    """
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, parentwidget, **kwargs)
        self.name = "Overlay"
        # Populate with toolbars
        self.vectorclip = VectorClipTB(self)
        self.vectorclip.pack(side="left", padx=3, pady=3)


# Toolbars

class VectorClipTB(tk.Frame):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, parentwidget)
        self.name = "Vector Clip"
        self.buttonframe = tk.Frame(self)
        self.buttonframe.pack(side="top")
        self.intersect = tk.Button(self.buttonframe, text="intersect", height=3)
        self.intersect.pack(side="left", padx=2, pady=2)
        self.union = tk.Button(self.buttonframe, text="union", height=3)
        self.union.pack(side="left", padx=2, pady=2)
        self.name_label = tk.Label(self, text=self.name)
        self.name_label.pack(side="top", fill="x")


class SelectionTB(tk.Frame):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, parentwidget)
        self.name = "Selection"
        self.buttonframe = tk.Frame(self)
        self.buttonframe.pack(side="top")
        self.select_rect = tk.Button(self.buttonframe, text="rectangle select", height=3)
        self.select_rect.pack(side="left", padx=2, pady=2)
        self.clear_select = tk.Button(self.buttonframe, text="clear selection", height=3)
        self.clear_select.pack(side="left", padx=2, pady=2)
        self.name_label = tk.Label(self, text=self.name)
        self.name_label.pack(side="top", fill="x")


class NavigateTB(tk.Frame):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, parentwidget, width=80, height=40)
        self.global_view = tk.Button(self, text="zoom global")
        self.global_view.pack(side="left", padx=2, pady=2)
        self.zoom_rect = tk.Button(self, text="zoom to rectangle")
        self.zoom_rect.pack(side="left", padx=2, pady=2)


# Panes

class LayersPane(tk.Frame):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, parentwidget, width=60)
        self["bg"] = "orange"
        
        # Outline around layer pane
        outline = tk.Frame(self, bg="Grey40")
        outline.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Make the top header
        header = tk.Label(outline, text="   Layers:", bg="black", fg="white", anchor="w", font=("Cambria", 16))
        header.place(relx=0.03, rely=0.01, relwidth=0.94, relheight=0.09, anchor="nw")
        
        # Button for adding new layer
        def selectfile():
            userchoice = askopenfilenames(filetypes=[("shapefiles",".shp")])
            for each in userchoice:
                print each
            #self.map.LoadShapefiles(inputshapefilepaths=userchoice)
        button_addlayer = tk.Button(header, text="+", bg="yellow", command=selectfile)
        button_addlayer.pack(side="right", anchor="e", ipadx=3, padx=6)

        # Then, the layer list view
        self.layersview = tk.Frame(outline, bg="white")
        self.layersview.place(relx=0.03, rely=0.1, relwidth=0.94, relheight=0.89)



# Status Bars

class StatusBar(tk.Frame):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, parentwidget, height=25)

class ProjectionStatus(tk.Label):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Label.__init__(self, parentwidget)

class ZoomStatus(tk.Label):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Label.__init__(self, parentwidget)

class MouseStatus(tk.Label):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Label.__init__(self, parentwidget)


# The Main Map

class MapView(tk.Label):
    def __init__(self, parentwidget, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Label.__init__(self, parentwidget, **kwargs)

        # Create the maprenderer
        self.renderer = ""
        self.proj = kwargs.get("projection", "WGS84")
        self["text"] = "mapview"
        self["bg"] = "purple"

    # Rendering
    def DrawShapefile(self, shapelygeoms, projection):
        Report("loading")
        geomstofeature = cartopy.feature.ShapelyFeature(geometries=shapelygeoms, crs=projection)
        Report("drawing")
        self.ax.add_feature(geomstofeature, facecolor="pink", edgecolor='green')
        self.ax.figure.canvas.draw()
    def UpdateLayersView(self, layerlist):
        if len(self.layerobjects) > 0:
            [self.layerobjects[layername].destroy() for layername in self.layerobjects]
            self.layerobjects.clear()
        for layer in layerlist:
            layerobj = Label(master=self.layersview, text=layer)
            layerobj.pack(side="top", fill="x")
            self.layerobjects.update( {layer:layerobj} )

    # Interactive
    def MouseMoving(self, event):
        self.coordsdisplay["text"] = str(event.xdata)+","+str(event.ydata)
        if event.button == 1 and self.mousepressed == True:
            self.PanMap(event.xdata, event.ydata)
    def MousePressed(self, event):
        self.clickcoords = (event.xdata, event.ydata)
        self.mousepressed = True
        timesincelastclick = time.time()-self.clicktime
        if timesincelastclick < 0.2:
            self.ZoomMap(event.xdata, event.ydata, event.button)
        self.clicktime = time.time()
    def MouseReleased(self, event):
        print "release"
        self.mousepressed = False
    def ZoomMap(self, eventx, eventy, eventbutton=0):
        if eventbutton == 1 and self.zoomtracker > 5:
            self.zoomtracker -= 5
        elif eventbutton == 3 and self.zoomtracker < 100:
            self.zoomtracker += 5
        zoompercent = self.zoomtracker/100.0
        xlim = (eventx/2.0-180*zoompercent, eventx/2.0+180*zoompercent)
        ylim = (eventy/2.0-90*zoompercent, eventy/2.0+90*zoompercent)
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)
        self.ax.figure.canvas.draw()
        self.zoomdisplay["text"] = "Showing "+str(int(self.zoomtracker))+"% of full extent"
    def PanMap(self, x, y):
        #first calc current extent
        zoompercent = self.zoomtracker/100.0
        current = self.ax.get_extent()
        #then determine mousemove and set new extent (plussing is to avoid negativ nrs when deteremning movediff
        xmoved = (self.clickcoords[0]+180)-(x+180)
        ymoved = (self.clickcoords[1]+90)-(y+90)
        xlim = ( current[0]+xmoved, current[1]+xmoved )
        ylim = ( current[2]+ymoved, current[3]+ymoved )
        self.ax.set_xlim(xlim)
        self.ax.set_ylim(ylim)
        self.ax.figure.canvas.draw()











