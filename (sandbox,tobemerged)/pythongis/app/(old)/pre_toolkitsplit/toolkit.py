
# Import builtins
import sys, os
import time
import inspect

# Import GUI library
import Tkinter as tk
from tkFileDialog import askopenfilenames, asksaveasfilename
import PIL, PIL.Image, PIL.ImageTk

# Import GIS functionality
import pythongis as pg



# Icons folder
APP_FOLDER = os.path.split(__file__)[0]
ICONS_FOLDER = os.path.join(APP_FOLDER, "icons")



# Some basic widgets
class IconButton(tk.Button):
    def __init__(self, master, **kwargs):
        tk.Button.__init__(self, master, **kwargs)

    def set_icon(self, iconname, **kwargs):
        img_path = os.path.join(ICONS_FOLDER, iconname)
        img = PIL.ImageTk.PhotoImage(PIL.Image.open(img_path))
        self.config(image=img, **kwargs)
        self.img = img


# The Ribbon/Tab system

class Ribbon(tk.Frame):
    """
    Can switch between a series of logically grouped toolbar areas (tabs).
    """
    current_color = "green"
    inactive_color = "pink"
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, height=120)

        # Make top area for tab selectors
        self.tabs_area = tk.Frame(self, height=30, bg=self.inactive_color)
        self.tabs_area.pack(fill="x", side="top")

        # Make bottom area for each tab's toolbars
        self.toolbars_area = tk.Frame(self, height=90, bg=self.current_color)
        self.toolbars_area.pack(fill="x", side="top")
        
        # Populate with tabs
        self.tabs = dict()
        hometab = HomeTab(self.toolbars_area, bg=self.current_color)
        self.add_tab(hometab)
        overlaytab = OverlayTab(self.toolbars_area, bg=self.current_color)
        self.add_tab(overlaytab)

        # Set starting tab
        self.switch(event=None, tabname="Home")

    def add_tab(self, tab):
        self.tabs[tab.name] = tab
        self.current = tab
        # add tab to toolbars area
        tab.place(relwidth=1, relheight=1)
        # add tabname to tab selector area
        tab.selector = tk.Label(self.tabs_area, text=tab.name, padx=10, pady=5)
        tab.selector.pack(side="left", padx=5)
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

class Tab(tk.Frame):
    """
    Base class for all tabs
    """
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **kwargs)

    def add_toolbar(self, toolbar):
        toolbar.pack(side="left", padx=10, pady=10)

class HomeTab(Tab):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **kwargs)
        self.name = "Home"

        # Add toolbars
        selection = SelectionTB(self)
        self.add_toolbar(selection)

class OverlayTab(Tab):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **kwargs)
        self.name = "Overlay"

        # Add toolbars
        vectorclip = VectorClipTB(self)
        self.add_toolbar(vectorclip)
        

# Toolbars

class Toolbar(tk.Frame):
    """
    Base class for all toolbars.
    """
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **kwargs)

        # Divide into button area and toolbar name
        self.buttonframe = tk.Frame(self)
        self.buttonframe.pack(side="top")
        self.name_label = tk.Label(self)
        self.name_label.pack(side="top", fill="x")

    def add_button(self, button):
        button.config(height=2)
        button.pack(side="left", padx=2, pady=2)

class VectorClipTB(Toolbar):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        Toolbar.__init__(self, master, **kwargs)
        self.name_label["text"] = "Vector Clip"

        # Add buttons
        intersect = tk.Button(self.buttonframe, text="intersect")
        self.add_button(intersect)
        union = tk.Button(self.buttonframe, text="union")
        self.add_button(union)

class SelectionTB(Toolbar):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        Toolbar.__init__(self, master, **kwargs)
        self.name_label["text"] = "Selection"

        # Add buttons
        intersect = tk.Button(self.buttonframe, text="rectangle select")
        self.add_button(intersect)
        union = tk.Button(self.buttonframe, text="clear selection")
        self.add_button(union)


# Special toolbars

class NavigateTB(tk.Frame):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **kwargs)

        # Modify some options
        self.config(width=80, height=40)

        # Add buttons
        self.global_view = tk.Button(self, text="zoom global")
        self.global_view.pack(side="left", padx=2, pady=2)
        self.zoom_rect = tk.Button(self, text="zoom to rectangle")
        self.zoom_rect.pack(side="left", padx=2, pady=2)


# Panes

class LayerItem(tk.Frame):
    def __init__(self, master, data, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **kwargs)

        # Modify some options
        self.config(width=60)

        # Create the visibility check box
        var = tk.IntVar()
        self.checkbutton = tk.Checkbutton(self, variable=var, offvalue=0, onvalue=1, command=self.toggle_visibility)
        self.checkbutton.var = var
        self.checkbutton.pack(side="left")
        self.checkbutton.select()

        # Create Delete button to the right
        self.deletebutton = IconButton(self, padx=2, relief="flat", command=self.delete)
        self.deletebutton.set_icon("delete_layer.png")
        self.deletebutton.pack(side="right")

        # Create the layername display
        self.data = data
        if self.data.filepath: 
            layername = os.path.split(self.data.filepath)[-1]
        else: layername = "Unnamed layer"
        self.namelabel = tk.Label(self, text=layername, anchor="w")
        self.namelabel.pack(side="left", fill="x")

        # Bind doubleclick, rightclick, and drag events
        self.namelabel.bind("<Button-3>", self.right_click)
        self.namelabel.bind("<Double-Button-1>", self.double_click)
        # ...

    def right_click(self, event):
        gui = event.widget._root().winfo_children()[0]     
        menu = RightClickMenu(gui, tearoff=0)
        
        # Add menu items
        menu.add_command(label="Rename")
        
        for methodname,method in inspect.getmembers(self.data, inspect.ismethod):
            if not methodname.startswith("_"):
                def runmethodwindow():
                    toolwin = RunToolWindow(self)
                    toolwin.title(methodname)
                    toolwin.set_target_method(method)
                    toolwin.transient()
                    toolwin.grab_set()
                menu.add_command(label=methodname, command=runmethodwindow)
                
        menu.add_command(label="Properties")
        menu.add_command(label="Save", command=self.save)

        # Place and show menu
        menu.post(event.x_root, event.y_root)

    def double_click(self, event):
        pass

    def toggle_visibility(self):
        self.checkbutton.toggle()
        #self.map.render()

    def delete(self):
        layerspane = self.master.master.master
        layerspane.remove_layer(self)

    def save(self):
        savepath = asksaveasfilename()
        self.data.save(savepath)

            

class LayersPane(tk.Frame):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **kwargs)

        # Modify some options
        self.config(width=60, bg="orange")
        
        # Outline around layer pane
        outline = tk.Frame(self, bg="Grey40")
        outline.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Make the top header
        header = tk.Label(outline, text="Layers:", bg="black", fg="white", anchor="w", padx=5)
        header.place(relx=0.03, rely=0.01, relwidth=0.94, relheight=0.09, anchor="nw")
        
        # Button for adding new layer
        def selectfiles():
            filepaths = askopenfilenames()
            for filepath in filepaths:
                self.load_layer(filepath)
        button_addlayer = IconButton(header, bg="yellow", command=selectfiles)
        button_addlayer.set_icon("add_layer.png")
        button_addlayer.pack(side="right", anchor="e", ipadx=3, padx=6)

        # Then, the layer list view
        self.layersview = tk.Frame(outline, bg="white")
        self.layersview.place(relx=0.03, rely=0.1, relwidth=0.94, relheight=0.89)

    def load_layer(self, filepath):
        try:
            if filepath.endswith((".shp",".geojson",".json",".gpx")):
                loaded = pg.GeoTable(filepath)
            elif filepath.endswith((".asc",".ascii",".tif",".tiff",".geotiff")):
                loaded = pg.MultiGrid(filepath)
            else:
                raise Exception()
        except:
            popup_message(self, "Unable to load file")
            return
        newlayer = LayerItem(self.layersview, data=loaded)
        newlayer.pack(fill="x")

    def remove_layer(self, layer):
        layer.destroy()
        #self.map.render()
        for layer in self.layersview.winfo_children():
            layer.pack(fill="x")
        



# Misc Popup Windows

def popup_message(parentwidget, errmsg):
    popup_window = tk.Toplevel(parentwidget)
    popup_window.transient()
    popup_window.grab_set()
    message = tk.Label(popup_window, text=errmsg)
    message.pack()
    def click_ok():
        popup_window.destroy()
    ok = tk.Button(popup_window, text="OK", command=click_ok)
    ok.pack()

class RightClickMenu(tk.Menu):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        tk.Menu.__init__(self, master, **kwargs)
  
class LayerOptionsWindow(tk.Toplevel):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        tk.Menu.__init__(self, master, **kwargs)

class RunToolWindow(tk.Toplevel):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Toplevel and add to it
        tk.Toplevel.__init__(self, master, **kwargs)

    def set_target_method(self, method):
        # automatically build input widgets from method arguments
        args, varargs, keywords, defaults = inspect.getargspec(method)
        for i, arg in enumerate(args):
            if arg == "self": continue
            tk.Label(self, text=arg).grid(row=i, column=0)
            tk.Entry(self).grid(row=i, column=1)
        # make cancel and run button at bottom
        tk.Button(self, text="Cancel").grid(row=i+1, column=0)
        tk.Button(self, text="Run Tool").grid(row=i+1, column=1)
    


# Status Bars

class StatusBar(tk.Frame):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **kwargs)

        # Modify some options
        self.config(height=25, bg="yellow")

        # Insert status items
        ProjectionStatus(self).pack(side="left")
        MouseStatus(self).pack(side="right")
        ZoomStatus(self).pack(side="right")

class ProjectionStatus(tk.Label):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Label and add to it
        tk.Label.__init__(self, master, text="Map Projection: ", **kwargs)

class ZoomStatus(tk.Label):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Label and add to it
        tk.Label.__init__(self, master, text="Zoom Percent: ", **kwargs)

class MouseStatus(tk.Label):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Label and add to it
        tk.Label.__init__(self, master, text="Mouse Coordinates:", **kwargs)


# The Main Map

class MapView(tk.Label):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Label and add to it
        tk.Label.__init__(self, master, **kwargs)

        # Create the maprenderer
        self.renderer = ""
        self.proj = kwargs.get("projection", "WGS84")
        self["text"] = "mapview"
        self["bg"] = "purple"
        
##    # Bind interactive events like zoom, pan, and select
####        self.zoomtracker = 100
####        self.clicktime = time.time()
####        self.mousepressed = False
####        self._parent.bind('button_press_event', self.MousePressed)
####        self._('button_release_event', self.MouseReleased)
####        self.mapframe.canvas.mpl_connect('motion_notify_event', self.MouseMoving)


    # Rendering
    def DrawLayer(self, shapelygeoms, projection):
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











