
# Import builtins
import sys, os

# Import GUI library
import Tkinter as tk
from .toolkit import *


class GUI(tk.Frame):
    def __init__(self, parentwidget, **kwargs):
        tk.Frame.__init__(self, parentwidget, **kwargs)
        self.parentwidget = parentwidget

        # Create top buttons
        ribbon = Ribbon(self)
        ribbon.pack(side="top", fill="x")#place(relwidth=1)

        ### Create main middle area
        middle_area = tk.Frame(self, bg="brown")
        middle_area.pack(side="top", expand=True, fill="both")#place(y=ribbon.cget("height"), relwidth=1, relheight=0.7)
        # Layers pane on left
        layer = LayersPane(middle_area)
        layer.place(relx=0, relwidth=0.15, relheight=1)
        # Mapwidget on right
        mapview = MapView(middle_area)
        mapview.place(relx=0.15, relwidth=0.85, relheight=1)
        # Attach floating navigation toolbar inside mapwidget
        navigation = NavigateTB(mapview)
        navigation.place(relx=0.5, rely=0, anchor="n")

        # Create bottom info and mouse coords bar at bottom
        statusbar = StatusBar(self)
        statusbar.pack(side="bottom", fill="x")
        


def run(mainbgcolor="light blue",
        bottominfobgcolor="black",
        bottominfotxtcolor="white"):
    """
    Build the GUI.
    """
    # create main window
    window = tk.Tk()
    window.wm_title("Python GIS")
    window.state('zoomed')

    # pack in the GUI frame
    gui = GUI(window, bg=mainbgcolor)
    gui.place(relwidth=1, relheight=1) #pack(expand=True, fill="both")
    
    # open the window
    window.mainloop()

    




