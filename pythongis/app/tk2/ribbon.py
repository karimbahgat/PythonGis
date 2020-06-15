
import sys
if sys.version.startswith("2"):
    import Tkinter as tk
else:
    import tkinter as tk
import ttk
from . import basics
from . import mixins as mx




# The Ribbon/Tab system

class Ribbon(mx.AllMixins, ttk.Frame):
    """
    Can switch between a series of logically grouped areas (tabs).
    """
    def __init__(self, master, **kwargs):

        self._anchor = kwargs.pop("anchor", "nw")
        if self._anchor.startswith("n"): side = "top"; fill="x"
        elif self._anchor.startswith("w"): side = "left"; fill="y"
        elif self._anchor.startswith("e"): side = "right"; fill="y"
        elif self._anchor.startswith("s"): side = "bottom"; fill="x"
        if len(self._anchor) == 1: fill=None

        # Make this class a subclass of tk.Frame and add to it
        ttk.Frame.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

        # Make top area for tab selectors
        self.selectors_area = ttk.Frame(self)
        self.selectors_area.pack(fill=fill, side=side)

        # Make bottom area for each tab's toolbars
        self.tab_area = ttk.Frame(self)
        self.tab_area.pack(fill="both", expand=True, side="top")
        #self.pack_propagate(False)

        # Create tab list
        self.tabs = dict()

    def add_tab(self, tabname):
        tab = Tab(self.tab_area, tabname=tabname)
        self.tabs[tab.name] = tab
        self.current = tab
        # add tab to toolbars area
        tab.grid(row=0, column=0, sticky="nsew")
        self.tab_area.grid_rowconfigure(0, weight=1)
        self.tab_area.grid_columnconfigure(0, weight=1)
        # add tabname to tab selector area
        if len(self._anchor) == 2:
            if self._anchor.endswith("n"): side = "top"
            elif self._anchor.endswith("w"): side = "left"
            elif self._anchor.endswith("e"): side = "right"
            elif self._anchor.endswith("s"): side = "bottom"
        elif len(self._anchor) == 1:
            if self._anchor.startswith("n"): side = "left"
            elif self._anchor.startswith("w"): side = "top"
            elif self._anchor.startswith("e"): side = "top"
            elif self._anchor.startswith("s"): side = "left"
        tab.selector = basics.Button(self.selectors_area, text=tab.name)
        tab.selector.pack(side=side, padx=5)
        # make tab selector selectable
##        def mouse_in(event):
##            if event.widget["state"] == "normal":
##                event.widget.config(style_tabselector_mouseover)
##        def mouse_out(event):
##            if event.widget["state"] == "normal":
##                event.widget.config(style_tabselector_normal)
##        tab.selector.bind("<Enter>", mouse_in)
##        tab.selector.bind("<Leave>", mouse_out)
        tab.selector.bind("<Button-1>", self.switch)
        return tab

    def switch(self, event=None, tabname=None):
        if event: tabname = event.widget["text"]
        if str(self.tabs[tabname].selector["state"])!= "disabled":
            # deactivate old tab
            self.current.selector.config(state="normal")#, relief="flat")
            # activate new tab
            self.current = self.tabs[tabname]
            self.current.selector.config(state="pressed")#, relief="ridge")
            self.current.lift()

class ListRibbon:
    # same as ribbon, but instead uses dropdown to switch tabs
    pass

class Tab(mx.AllMixins, ttk.Frame):
    """
    Base class for all tabs
    """
    def __init__(self, master, tabname, **kwargs):
        
        # Make this class a subclass of tk.Frame and add to it
        ttk.Frame.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

        # remember name
        self.name = tabname






