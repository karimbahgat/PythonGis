import Tkinter as tk
from .buttons import *
from .popups import *
from ... import vector
from ... import raster

# Import style
from . import theme
style_toolbar_normal = {"bg": theme.color4,
                        "pady": 0}
style_namelabel_normal = {"bg": theme.color4,
                          "font": theme.font2["type"],
                          "fg": theme.font2["color"],
                          "pady": 0}



# Toolbars

class Toolbar(tk.Frame):
    """
    Base class for all toolbars.
    """
    def __init__(self, master, toolbarname, **kwargs):
        # get theme style
        style = style_toolbar_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **style)

        # Divide into button area and toolbar name
        self.buttonframe = tk.Frame(self, **style)
        self.buttonframe.pack(side="top", fill="y", expand=True)
        self.name_label = tk.Label(self, **style_namelabel_normal)
        self.name_label["text"] = toolbarname
        self.name_label.pack(side="bottom")

    def add_button(self, icon=None, **kwargs):
        button = IconButton(self.buttonframe)
        options = {"text":"", "width":48, "height":32, "compound":"top"}
        options.update(kwargs)
        if icon:
            button.set_icon(icon, **options)
        else:
            button.config(**options)
        button.pack(side="left", padx=2, pady=0, anchor="center")
        return button

class VectorFilesTB(Toolbar):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        Toolbar.__init__(self, master, **kwargs)
        self.name_label["text"] = "Vector Files"

        # Add buttons
        def open_options_window():
            VectorMergeOptionWindow(self)
        merge = IconButton(self.buttonframe, text="Merge", 
                           command=open_options_window)
        merge.set_icon("vector_merge.png", width=48, height=32, compound="top")
        self.add_button(merge)

class VectorClipTB(Toolbar):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Frame and add to it
        Toolbar.__init__(self, master, **kwargs)
        self.name_label["text"] = "Vector Clip"

        # Add buttons
        intersect = Button(self.buttonframe, text="intersect")
        self.add_button(intersect)
        union = Button(self.buttonframe, text="union")
        self.add_button(union)


##class SelectionTB(Toolbar):
##    def __init__(self, master, **kwargs):
##        # Make this class a subclass of tk.Frame and add to it
##        Toolbar.__init__(self, master, **kwargs)
##        self.name_label["text"] = "Selection"
##
##        # Add buttons
##        intersect = Button(self.buttonframe, text="rectangle select")
##        self.add_button(intersect)
##        union = Button(self.buttonframe, text="clear selection")
##        self.add_button(union)


# Special toolbars

class NavigateTB(tk.Frame):
    def __init__(self, master, **kwargs):
        # get theme style
        style = style_toolbar_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **style)

        # Modify some options
        self.config(width=80, height=40)

    def assign_mapview(self, mapview):
        mapview.naviation = self
        self.mapview = mapview

        # Add buttons
        self.global_view = IconButton(self, text="zoom global", command=self.mapview.zoom_global)
        self.global_view.set_icon("zoom_global.png", width=32, height=32)
        self.global_view.pack(side="left", padx=2, pady=2)
        self.zoom_rect = IconButton(self, text="zoom to rectangle", command=self.mapview.zoom_rect)
        self.zoom_rect.set_icon("zoom_rect.png", width=32, height=32)
        self.zoom_rect.pack(side="left", padx=2, pady=2)
        


        
       
