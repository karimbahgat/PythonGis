import Tkinter as tk
from .toolbars import *


# Import style
from . import theme
style_ribbon_normal = {"bg": theme.color3,
                       "height": 120,
                       "pady": 0}


style_tabsarea_normal = {"bg": theme.color3,
                         "height": 20,
                         "padx": 1,
                         "pady": 0}


style_tabselector_normal = {"bg": theme.color3,
                            "activebackground": theme.color4,
                            "fg": theme.font1["color"],
                            "font": theme.font1["type"],
                            "relief": "flat",
                            "padx":10, "pady":5}
style_tabselector_mouseover = {"bg": "Grey93" }


style_toolbarsarea_normal = {"bg": theme.color4,
                           }#"height": 90}




# The Ribbon/Tab system

class Ribbon(tk.Frame):
    """
    Can switch between a series of logically grouped toolbar areas (tabs).
    """
    def __init__(self, master, **kwargs):
        # get theme style
        style = style_ribbon_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **style)

        # Make top area for tab selectors
        self.tabs_area = tk.Frame(self, **style_tabsarea_normal)
        self.tabs_area.pack(fill="x", side="top")

        # Make bottom area for each tab's toolbars
        self.toolbars_area = tk.Frame(self, **style_toolbarsarea_normal)
        self.toolbars_area.pack(fill="both", expand=True, side="top")
        self.pack_propagate(False)

        # Create tab list
        self.tabs = dict()
        
##        # Populate with tabs
##        self.tabs = dict()
##        hometab = HomeTab(self.toolbars_area)
##        self.add_tab(hometab)
##        managetab = ManagementTab(self.toolbars_area)
##        self.add_tab(managetab)
##        overlaytab = OverlayTab(self.toolbars_area)
##        self.add_tab(overlaytab)
##        
##        # Set starting tab
##        self.switch(event=None, tabname="Home")

    def add_tab(self, tabname):
        tab = Tab(self.toolbars_area, tabname=tabname)
        self.tabs[tab.name] = tab
        self.current = tab
        # add tab to toolbars area
        tab.place(relwidth=1, relheight=1)
        # add tabname to tab selector area
        tab.selector = tk.Label(self.tabs_area, text=tab.name, **style_tabselector_normal)
        tab.selector.pack(side="left", padx=5)
        # make tab selector selectable
        def mouse_in(event):
            if event.widget["state"] == "normal":
                event.widget.config(style_tabselector_mouseover)
        def mouse_out(event):
            if event.widget["state"] == "normal":
                event.widget.config(style_tabselector_normal)
        tab.selector.bind("<Enter>", mouse_in)
        tab.selector.bind("<Leave>", mouse_out)
        tab.selector.bind("<Button-1>", self.switch)
        return tab

    def switch(self, event=None, tabname=None):
        if event: tabname = event.widget["text"]
        # deactivate old tab
        #self.current.selector.config(style_tabselector_inactive)
        self.current.selector["state"] = "normal"
        # activate new tab
        self.current = self.tabs[tabname]
        self.current.selector.config(style_tabselector_normal)
        self.current.selector["state"] = "active"
        print tabname, self.current
        self.current.lift()

    def assign_statusbar(self, statusbar):
        self.statusbar = statusbar

class Tab(tk.Frame):
    """
    Base class for all tabs
    """
    def __init__(self, master, tabname, **kwargs):
        # get theme style
        style = style_toolbarsarea_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **style)

        # remember name
        self.name = tabname

    def add_toolbar(self, toolbarname):
        toolbar = Toolbar(self, toolbarname=toolbarname)
        toolbar.pack(side="left", padx=10, pady=0, fill="y")
        return toolbar

##class HomeTab(Tab):
##    def __init__(self, master, **kwargs):
##        # Make this class a subclass of tk.Frame and add to it
##        Tab.__init__(self, master, **kwargs)
##        self.name = "Home"
##
##        # Add toolbars
####        selection = SelectionTB(self)
####        self.add_toolbar(selection)
##
##class ManagementTab(Tab):
##    def __init__(self, master, **kwargs):
##        # Make this class a subclass of tk.Frame and add to it
##        Tab.__init__(self, master, **kwargs)
##        self.name = "Management"
##
##        # Add toolbars
##        vectorfiles = VectorFilesTB(self)
##        self.add_toolbar(vectorfiles)
##        
##class OverlayTab(Tab):
##    def __init__(self, master, **kwargs):
##        # Make this class a subclass of tk.Frame and add to it
##        Tab.__init__(self, master, **kwargs)
##        self.name = "Overlay"
##
##        # Add toolbars
##        vectorclip = VectorClipTB(self)
##        self.add_toolbar(vectorclip)
