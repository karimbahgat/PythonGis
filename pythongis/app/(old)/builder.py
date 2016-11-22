
# Import builtins
import sys, os
import time

# Import GUI library
import Tkinter as tk

# Import internals
from .toolkit import *
from .dialogues import *

# Import GIS functionality
import pythongis as pg


class GUI(tk.Frame):
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        # ------------------
        # Create a layergroup that keeps track of all the loaded data
        # ...so that all widgets can have access to the same data
        # ------------------
        self.layers = pg.renderer.LayerGroup()


        # -----------------
        # Place top ribbon area with tabs, toolbars, and buttons
        # -----------------
        self.ribbon = Ribbon(self)
        self.ribbon.pack(side="top", fill="x")
        # -----
        ## Home tab
        hometab = self.ribbon.add_tab("Home")
        # -----
        ## Visualize tab
        visitab = self.ribbon.add_tab("Visualize")
        ### (Output toolbar)
        output = visitab.add_toolbar("Output")
        def save_image():
            filepath = asksaveasfilename()
            self.mapview.renderer.img.save(filepath)
        output.add_button(text="Save Image", icon="save_image.png",
                               command=save_image)
        ## Management tab
        managetab = self.ribbon.add_tab("Manage")
        ### (Vector toolbar)
        vectorfiles = managetab.add_toolbar("Vector Files")
        def open_merge_window():
            window = VectorMergeOptionWindow(self, self.layerspane, self.statusbar)
        vectorfiles.add_button(text="Merge", icon="vector_merge.png",
                               command=open_merge_window)
        ### (Raster toolbar)
        rasterfiles = managetab.add_toolbar("Raster Files")
        def open_mosaic_window():
            window = RasterMosaicOptionWindow(self, self.layerspane, self.statusbar)
        rasterfiles.add_button(text="Mosaic", icon="mosaic.png",
                               command=open_mosaic_window)
        ## Analysis tab
        analysistab = self.ribbon.add_tab("Analyze")
        ### (Vector toolbar)
        vectorfiles = analysistab.add_toolbar("Vector")
        def open_overlapsummary_window():
            window = VectorOverlapSummaryWindow(self, self.layerspane, self.statusbar)
        vectorfiles.add_button(text="Overlap Summary", icon="overlap.png",
                               command=open_overlapsummary_window)
        ### (Raster toolbar)
        rasterfiles = analysistab.add_toolbar("Raster")
        def open_zonalstats_window():
            window = RasterZonalStatsOptionWindow(self, self.layerspane, self.statusbar)
        rasterfiles.add_button(text="Zonal statistics", icon="zonalstats.png",
                               command=open_zonalstats_window)

        # ------
        ## Set starting tab
        self.ribbon.switch(tabname="Home")


        # ---------------
        # Place main middle area
        # ---------------
        middle_area = tk.Frame(self)
        middle_area.pack(side="top", expand=True, fill="both")


        # ----------------
        # Layers pane on left
        # ----------------
        self.layerspane = LayersPane(middle_area)
        self.layerspane.pack(side="left", fill="y")

        # Bind layeritem right click behavior
        def layer_rightclick(event):
            layeritem = event.widget.master.master
            if isinstance(layeritem.renderlayer, pg.renderer.VectorLayer):
                menu = RightClickMenu_VectorLayer(self, self.layerspane, layeritem, self.statusbar)
            elif isinstance(layeritem.renderlayer, pg.renderer.RasterLayer):
                menu = RightClickMenu_RasterLayer(self, self.layerspane, layeritem, self.statusbar)
            # Place and show menu
            menu.post(event.x_root, event.y_root)      
        self.layerspane.bind_layer_rightclick(layer_rightclick)
        
        # Place add layer button in the header of the layerspane
        def selectfiles():
            filepaths = askopenfilenames()
            encoding = self.data_options.get("encoding")
            for filepath in filepaths:
                self.layerspane.add_layer(filepath, encoding=encoding)
        button_addlayer = IconButton(self.layerspane.header, command=selectfiles)
        button_addlayer.set_icon("add_layer.png", width=27, height=27)
        button_addlayer.pack(side="right", anchor="e", ipadx=3, padx=6, pady=3,)

        # Place button for setting data options
        self.data_options = {"encoding": "utf8"}
        button_data_options = IconButton(self.layerspane.header)
        button_data_options.set_icon("data_options.png", width=24, height=21)
        button_data_options.pack(side="right", anchor="e", ipadx=5, ipady=3, padx=6, pady=3,)

        # Open options window on button click
        def data_options_window():
            win = popups.Window(self)
            runtool = popups.RunToolFrame(win)
            runtool.pack(fill="both", expand=True)
            
            # assign status bar
            runtool.assign_statusbar(self.statusbar)
            
            # place option input for data encoding
            runtool.add_option_input("Vector data encoding", valuetype=str,
                                 argname="encoding", default=self.data_options.get("encoding"))
            
            # when clicking OK, update data options
            def change_data_options(*args, **kwargs):
                """
                Customize settings for loading and saving data.

                Vector data encoding: Common options include "utf8" or "latin"
                """
                # update user settings
                self.data_options.update(kwargs)
                
            def change_data_options_complete(result):
                # close window
                win.destroy()
                
            runtool.set_target_method("Changing data options", change_data_options)
            runtool.set_finished_method(change_data_options_complete)
            
        button_data_options["command"] = data_options_window



        # -----------------
        # Mapwidget on right
        # -----------------
        self.mapview = MapView(middle_area)
        self.mapview.pack(side="left", fill="both", expand=True)
        
        # Attach floating navigation toolbar inside mapwidget
        self.navigation = NavigateTB(self.mapview)
        self.navigation.place(relx=0.5, rely=0.03, anchor="n")
        self.navigation.assign_mapview(self.mapview)


        # ------------------
        # Place statusbar at the bottom
        # ------------------
        self.statusbar = StatusBar(self, height=20, width=100)
        self.statusbar.pack(side="bottom", fill="x")


        # ------------
        # Assign statusbar to widgets that perform actions
        # ------------
        self.mapview.assign_statusbar(self.statusbar)
        self.layerspane.assign_statusbar(self.statusbar)

        # ------------
        # Assign layergroup to layerspane and mapview
        # ------------  
        self.layerspane.assign_layergroup(self.layers)
        self.mapview.assign_layergroup(self.layers)






        



def run():
    """
    Build the GUI.
    """
    # create main window
    window = tk.Tk()
    window.wm_title("Python GIS")
    try: # windows and mac
        window.wm_state('zoomed')
    except: # linux
        window.wm_attributes("-zoomed", "1")
    window.geometry("1000x500")

    # assign logo from same directory as this file
    import sys,os
    curfolder,curfile = os.path.split(__file__)
    logopath = os.path.join(curfolder, "logo.ico")
    window.iconbitmap(logopath)

    # pack in the GUI frame
    gui = GUI(window)
    gui.place(relwidth=1, relheight=1)
    
    # open the window
    window.mainloop()

    




