
# Import builtins
import sys, os
import time

# Import GUI library
import Tkinter as tk
from .toolkit import *
from .dialogues import *
import pythongis as pg


class GUI(tk.Frame):
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        # ------------------
        # Create a layergroup that keeps track of all the loaded data
        # ...so that all widgets can have access to the same data
        # ------------------
        self.layers = pg.LayerGroup()


        # -----------------
        # Place top ribbon area with tabs, toolbars, and buttons
        # -----------------
        self.ribbon = Ribbon(self)
        self.ribbon.pack(side="top", fill="x")
        # -----
        ## Home tab
        hometab = self.ribbon.add_tab("Home")
        # -----
        ## Management tab
        managetab = self.ribbon.add_tab("Management")
        ### (Vector toolbar)
        vectorfiles = managetab.add_toolbar("Vector Files")
        def open_merge_window():
            window = VectorMergeOptionWindow(self, self.layerspane)
            window.assign_statusbar(self.statusbar)
        vectorfiles.add_button(text="Merge", icon="vector_merge.png",
                               command=open_merge_window)
        ### (Raster toolbar)
        rasterfiles = managetab.add_toolbar("Raster Files")
        def open_mosaic_window():
            window = RasterMosaicOptionWindow(self, self.layerspane)
            window.assign_statusbar(self.statusbar)
        rasterfiles.add_button(text="Mosaic", icon="mosaic.png",
                               command=open_mosaic_window)
        ## Analysis tab
        managetab = self.ribbon.add_tab("Analysis")
        ### (Vector toolbar)
        vectorfiles = managetab.add_toolbar("Vector")
        def open_overlapsummary_window():
            window = VectorOverlapSummaryWindow(self, self.layerspane)
            window.assign_statusbar(self.statusbar)
        vectorfiles.add_button(text="Overlap Summary", icon="overlap.png",
                               command=open_overlapsummary_window)
        ### (Raster toolbar)
        rasterfiles = managetab.add_toolbar("Raster")
        def open_zonalstats_window():
            window = RasterZonalStatsOptionWindow(self, self.layerspane)
            window.assign_statusbar(self.statusbar)
        rasterfiles.add_button(text="Zonal statistics", icon="zonalstats.png",
                               command=open_zonalstats_window)

        # ------
        ## Set starting tab
        self.ribbon.switch(tabname="Management")


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
            if isinstance(layeritem.renderlayer, pg.VectorLayer):
                menu = RightClickMenu_VectorLayer(self, self.layerspane, layeritem, self.statusbar)
            elif isinstance(layeritem.renderlayer, pg.RasterLayer):
                menu = RightClickMenu_RasterLayer(self, self.layerspane, layeritem, self.statusbar)
            # Place and show menu
            menu.post(event.x_root, event.y_root)      
        self.layerspane.bind_layer_rightclick(layer_rightclick)
        
        # Place add layer button in the header of the layerspane
        def selectfiles():
            filepaths = askopenfilenames()
            for filepath in filepaths:
                self.layerspane.add_layer(filepath)
        button_addlayer = IconButton(self.layerspane.header, command=selectfiles)
        button_addlayer.set_icon("add_layer.png", width=27, height=27)
        button_addlayer.pack(side="right", anchor="e", ipadx=3, padx=6, pady=3,)


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
        # not sure....
        # ------------
        
        ## ...assign to each of the primary widgets
        self.mapview.assign_statusbar(self.statusbar)
        self.layerspane.assign_statusbar(self.statusbar)
        
        ## ...assign to the layerspane and mapview
        self.layerspane.assign_layergroup(self.layers)
        self.mapview.assign_layergroup(self.layers)




        # TEMP TESTING
        def find_feat(event):
            print event.x, event.y
            x,y = self.mapview.renderer.pixel2coord(event.x, event.y)
            print x,y
            for layer in self.mapview.layers:
                # raster
                col,row = layer.data.geo_to_cell(x,y)
                print col,row
                for grid in layer.data.grids:
                    cell = grid.get( col,row )
                    print cell
                    for cell in cell.neighbours:
                        grid.set(cell.x,cell.y,255) #mark a ring
                
                # vector
                feats = layer.data.quick_overlap([x,y,x,y])
                for feat in feats:
                    print feat.row
                    
        self.mapview.bind("<ButtonRelease-3>", find_feat)



##        # Test progress
##        progress = ProgressBar(statusbar, width=200, height=20)
##        progress.pack(side="left")
##
##        import Queue
##        import threading
##        from . import helpers
##        queue = Queue.LifoQueue()
##        progress.listen(queue, update_ms=30, message="testing1...")
##        def test():
##            for x in helpers.trackloop(range(100000), queue, 1):
##                pass
##            print "finished", x
##        def test_thread():
##            t = threading.Thread(target=test)
##            t.daemon = True
##            t.start()
##            
##        self.after(1000, test_thread)






def run():
    """
    Build the GUI.
    """
    # create main window
    window = tk.Tk()
    window.wm_title("Python GIS")
    window.state('zoomed')
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

    




