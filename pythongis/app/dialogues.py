
import Tkinter as tk
import ScrolledText as tkst # a convenience module that ships with Tkinter

from .toolkit.popups import *
from .toolkit.ribbon import *
from .toolkit import theme
from . import icons
from .. import vector, raster

style_layeroptions_info = {"fg": theme.font1["color"],
                            "font": theme.font1["type"],
                            "relief": "flat"}


# DEFINE THE TOOL-SPECIFIC DIALOGUE WINDOWS

class LayerOptionsWindow(Window):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        Window.__init__(self, master, **kwargs)

        # Make the top ribbon selector
        self.ribbon = Ribbon(self)
        self.ribbon.pack(side="top", fill="both", expand=True)

    def add_info(self, tab, label, value):
        row = tk.Frame(tab, bg=tab.cget("bg"))
        row.pack(fill="x", anchor="n", pady=5, padx=5)
        
        # place label
        header = tk.Label(row, text=label, bg=tab.cget("bg"), **style_layeroptions_info)
        header.pack(side="left", anchor="nw", padx=3)
        
        # place actual info text
        value = str(value)
        info = tk.Entry(row, width=400, disabledbackground="white", justify="right", **style_layeroptions_info)
        info.pack(side="right", anchor="ne", padx=3)
        info.insert(0, value)
        info.config(state="readonly")
        return info

class VectorLayerOptionsWindow(LayerOptionsWindow):
    def __init__(self, master, layeritem, statusbar, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        LayerOptionsWindow.__init__(self, master, **kwargs)
        self.layeritem = layeritem

        ###########
        ### GENERAL OPTIONS TAB
        general = self.ribbon.add_tab("General")
        
        # add pieces of info
        self.source = self.add_info(general, "Source file: ", layeritem.renderlayer.data.filepath)
        self.proj = self.add_info(general, "Projection: ", self.layeritem.renderlayer.data.crs)
        self.bbox = self.add_info(general, "Bounding box: ", layeritem.renderlayer.data.bbox)
        self.fields = self.add_info(general, "Attribute fields: ", layeritem.renderlayer.data.fields)
        self.rows = self.add_info(general, "Total rows: ", len(layeritem.renderlayer.data))

        ###########
        ### SYMBOLOGY TAB
        symbols = self.ribbon.add_tab("Symbology")

        # With test symbology window on button click
        layeritem = self.layeritem
        frame = RunToolFrame(symbols)
        frame.pack(fill="both", expand=True)
        
        # assign status bar
        frame.assign_statusbar(statusbar)
        
        # place option input for data encoding
        frame.add_option_input("Fill size", valuetype=eval,
                             argname="fillsize", default=layeritem.renderlayer.styleoptions.get("fillsize"))
        frame.add_option_input("Fill color", valuetype=eval,
                             argname="fillcolor", default=layeritem.renderlayer.styleoptions.get("fillcolor"))
        frame.add_option_input("Outline color", valuetype=eval,
                             argname="outlinecolor", default=layeritem.renderlayer.styleoptions.get("outlinecolor"))
        frame.add_option_input("Outline width", valuetype=eval,
                             argname="outlinewidth", default=layeritem.renderlayer.styleoptions.get("outlinewidth"))
        
        # when clicking OK, update data options
        def change_symbol_options(*args, **kwargs):
            """
            Symbolize data. 
            """
            # update user settings
            layeritem.renderlayer.styleoptions.update(kwargs)
            
        def change_symbol_options_complete(result):
            # refresh layer and map
            for mapcanvas in layeritem.layerspane.layers.connected_maps:
                mapcanvas.render_one(layeritem.renderlayer)
                mapcanvas.mapview.update_image()
            # close window
            self.destroy()
            
        frame.set_target_method("Changing symbol options", change_symbol_options)
        frame.set_finished_method(change_symbol_options_complete)

        ###########
        # Set starting tab
        self.ribbon.switch(tabname="General")

class RasterLayerOptionsWindow(LayerOptionsWindow):
    def __init__(self, master, layeritem, statusbar, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        LayerOptionsWindow.__init__(self, master, **kwargs)
        self.layeritem = layeritem

        ###########
        ### GENERAL OPTIONS TAB
        general = self.ribbon.add_tab("General")

        # add pieces of info
        self.source = self.add_info(general, "Source file: ", layeritem.renderlayer.data.filepath)
        self.proj = self.add_info(general, "Projection: ", self.layeritem.renderlayer.data.crs)
        self.dims = self.add_info(general, "Dimensions: ", "%i, %i"%(self.layeritem.renderlayer.data.width,
                                                                     self.layeritem.renderlayer.data.height))
        self.bands = self.add_info(general, " Raster bands: ", "%i"%len(self.layeritem.renderlayer.data.bands))
        self.transform = self.add_info(general, "Transform: ", self.layeritem.renderlayer.data.info)
        self.bbox = self.add_info(general, "Bounding box: ", layeritem.renderlayer.data.bbox)

        ###########
        # Set starting tab
        self.ribbon.switch(tabname="General")

################  

class RightClickMenu_VectorLayer(tk.Menu):
    def __init__(self, master, layerspane, layeritem, statusbar, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        tk.Menu.__init__(self, master, tearoff=0, **kwargs)
        self.layerspane = layerspane
        self.layeritem = layeritem
        self.statusbar = statusbar
        self.imgs = dict()

        # Renaming
        self.imgs["rename"] = icons.get("rename.png", width=32, height=32)
        self.add_command(label="Rename", command=self.layeritem.ask_rename, image=self.imgs["rename"], compound="left")

        # Saving
        def ask_save():
            savepath = asksaveasfilename()
            self.statusbar.task.start("Saving layer to file...")
            pending = dispatch.request_results(self.layeritem.renderlayer.data.save, args=[savepath])
            def finish(result):
                if isinstance(result, Exception):
                    popup_message(self, str(result) + "\n\n" + savepath)
                self.statusbar.task.stop()
            dispatch.after_completion(self, pending, finish)
        self.imgs["save"] = icons.get("save.png", width=32, height=32)
        self.add_command(label="Save as", command=ask_save, image=self.imgs["save"], compound="left")

        # ---(Breakline)---
        self.add_separator()

        # Splitting
        def open_options_window():
            window = VectorSplitOptionWindow(self.layeritem, self.layerspane, self.layeritem, statusbar)
        self.imgs["split"] = icons.get("split.png", width=32, height=32)
        self.add_command(label="Split to layers", command=open_options_window, image=self.imgs["split"], compound="left")

        # ---(Breakline)---
        self.add_separator()

        # Buffering
        def open_options_window():
            window = VectorBufferOptionWindow(self.layeritem, self.layerspane, self.layeritem, statusbar)
        self.imgs["buffer"] = icons.get("buffer.png", width=32, height=32)
        self.add_command(label="Buffer", command=open_options_window, image=self.imgs["buffer"], compound="left")

        # Cleaning
        def open_options_window():
            window = VectorCleanOptionWindow(self.layeritem, self.layerspane, self.layeritem, statusbar)
        self.imgs["clean"] = icons.get("clean.png", width=32, height=32)
        self.add_command(label="Clean Geometries", command=open_options_window, image=self.imgs["clean"], compound="left")
                
        # ---(Breakline)---
        self.add_separator()
        
        # View properties
        def view_properties():
            window = VectorLayerOptionsWindow(self.layeritem, self.layeritem, statusbar)
        self.imgs["properties"] = icons.get("properties.png", width=32, height=32)
        self.add_command(label="Properties", command=view_properties, image=self.imgs["properties"], compound="left")
        

class RightClickMenu_RasterLayer(tk.Menu):
    def __init__(self, master, layerspane, layeritem, statusbar, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        tk.Menu.__init__(self, master, tearoff=0, **kwargs)
        self.layerspane = layerspane
        self.layeritem = layeritem
        self.statusbar = statusbar
        self.imgs = dict()

        # Renaming
        self.imgs["rename"] = icons.get("rename.png", width=32, height=32)
        self.add_command(label="Rename", command=self.layeritem.ask_rename, image=self.imgs["rename"], compound="left")
       
        # Saving
        def ask_save():
            savepath = asksaveasfilename()
            self.statusbar.task.start("Saving layer to file...")
            pending = dispatch.request_results(self.layeritem.renderlayer.data.save, args=[savepath])
            def finish(result):
                if isinstance(result, Exception):
                    popup_message(self, str(result) + "\n\n" + savepath)
                self.statusbar.task.stop()
            dispatch.after_completion(self, pending, finish)
        self.imgs["save"] = icons.get("save.png", width=32, height=32)
        self.add_command(label="Save as", command=ask_save, image=self.imgs["save"], compound="left")

        # ---(Breakline)---
        self.add_separator()

        # Resampling
        def open_options_window():
            window = RasterResampleOptionWindow(self.layeritem, self.layerspane, self.layeritem, statusbar)
        self.imgs["resample"] = icons.get("resample.png", width=32, height=32)
        self.add_command(label="Resample", command=open_options_window, image=self.imgs["resample"], compound="left")

        # ---(Breakline)---
        self.add_separator()
        
        # View properties
        def view_properties():
            window = RasterLayerOptionsWindow(self.layeritem, self.layeritem, statusbar)
        self.imgs["properties"] = icons.get("properties.png", width=32, height=32)
        self.add_command(label="Properties", command=view_properties, image=self.imgs["properties"], compound="left")

#################

class VectorCleanOptionWindow(Window):
    def __init__(self, master, layerspane, layeritem, statusbar, **kwargs):
        # Make this class a subclass and add to it
        Window.__init__(self, master, **kwargs)

        # Create runtoolframe
        self.runtool = RunToolFrame(self)
        self.runtool.pack(fill="both", expand=True)
        self.runtool.assign_statusbar(statusbar)

        # Add a hidden option from its associated layeritem data
        self.runtool.add_hidden_option(argname="data", value=layeritem.renderlayer.data)

        # Set the remaining options
        self.runtool.set_target_method("Cleaning data...", vector.manager.clean)
        self.runtool.add_option_input(argname="tolerance", label="Tolerance (in distance units)",
                             valuetype=float, default=0.0, minval=0.0, maxval=1.0)

        # Define how to process
        newname = layeritem.namelabel["text"] + "_cleaned"
        def process(result):
            if isinstance(result, Exception):
                popup_message(self, "Failed to clean the data:" + "\n\n" + str(result) )
            else:
                layerspane.add_layer(result, name=newname)
                self.destroy()
                
        self.runtool.set_finished_method(process)

class VectorSplitOptionWindow(Window):
    def __init__(self, master, layerspane, layeritem, statusbar, **kwargs):
        # Make this class a subclass and add to it
        Window.__init__(self, master, **kwargs)

        # Create runtoolframe
        self.runtool = RunToolFrame(self)
        self.runtool.pack(fill="both", expand=True)
        self.runtool.assign_statusbar(statusbar)

        # Add a hidden option from its associated layeritem data
        self.runtool.add_hidden_option(argname="data", value=layeritem.renderlayer.data)

        # Set the remaining options
        self.runtool.set_target_method("Splitting data...", vector.manager.split)
        self.runtool.add_option_input(argname="splitfields",
                              label="Split by fields",
                              multi=True, choices=layeritem.renderlayer.data.fields,
                              valuetype=str)

        # Define how to process
        def process(result):
            if isinstance(result, Exception):
                popup_message(self, "Failed to split the data:" + "\n\n" + str(result) )
            else:
                for splitdata in result:
                    layerspane.add_layer(splitdata)
                    self.update()
                self.destroy()
        self.runtool.set_finished_method(process)

class VectorBufferOptionWindow(Window):
    def __init__(self, master, layerspane, layeritem, statusbar, **kwargs):
        # Make this class a subclass and add to it
        Window.__init__(self, master, **kwargs)

        # Create runtoolframe
        self.runtool = RunToolFrame(self)
        self.runtool.pack(fill="both", expand=True)
        self.runtool.assign_statusbar(statusbar)

        # Add a hidden option from its associated layeritem data
        self.runtool.add_hidden_option(argname="data", value=layeritem.renderlayer.data)

        # Set the remaining options
        self.runtool.set_target_method("Buffering data...", vector.analyzer.buffer)
        self.runtool.add_option_input(argname="dist_expression",
                              label="Distance calculation",
                              valuetype=str)

        # Define how to process
        def process(result):
            if isinstance(result, Exception):
                popup_message(self, "Failed to buffer the data:" + "\n\n" + str(result) )
            else:
                layerspane.add_layer(result)
                self.destroy()
        self.runtool.set_finished_method(process)

class RasterResampleOptionWindow(Window):
    def __init__(self, master, layerspane, layeritem, statusbar, **kwargs):
        # Make this class a subclass and add to it
        Window.__init__(self, master, **kwargs)

        # Create runtoolframe
        self.runtool = RunToolFrame(self)
        self.runtool.pack(fill="both", expand=True)
        self.runtool.assign_statusbar(statusbar)

        # Add a hidden option from its associated layeritem data
        self.runtool.add_hidden_option(argname="raster", value=layeritem.renderlayer.data)

        # Set the remaining options
        self.runtool.set_target_method("Resampling data...", raster.manager.resample)
        def get_data_from_layername(name):
            data = None
            for layeritem in layerspane:
                if layeritem.name_label["text"] == name:
                    data = layeritem.renderlayer.data
                    break
            return data
        self.runtool.add_option_input(argname="width", label="Raster width (in cells)",
                                valuetype=int)
        self.runtool.add_option_input(argname="height", label="Raster height (in cells)",
                                valuetype=int)
        self.runtool.add_option_input(argname="cellwidth", label="Cell width (in distance units)",
                                valuetype=float)
        self.runtool.add_option_input(argname="cellheight", label="Cell height (in distance units)",
                                valuetype=float)
        # Define how to process after finished
        def process(result):
            if isinstance(result, Exception):
                popup_message(self, "Failed to resample the data:" + "\n\n" + str(result) )
            else:
                layerspane.add_layer(result)
                self.destroy()
        self.runtool.set_finished_method(process)


##############
# Multi Input

class VectorMergeOptionWindow(Window):
    def __init__(self, master, layerspane, statusbar, **kwargs):
        # Make this class a subclass and add to it
        Window.__init__(self, master, **kwargs)

        # Create runtoolframe
        self.runtool = RunToolFrame(self)
        self.runtool.pack(fill="both", expand=True)
        self.runtool.assign_statusbar(statusbar)
        
        # Set the remaining options
        self.runtool.set_target_method("Merging data...", vector.manager.merge)
        def get_data_from_layername(name):
            data = None
            for layeritem in layerspane:
                if layeritem.namelabel["text"] == name:
                    data = layeritem.renderlayer.data
                    break
            return data
        self.runtool.add_option_input(argname=None,
                              label="Layers to be merged",
                              multi=True,
                              choices=[layeritem.namelabel["text"] for layeritem in layerspane],
                              valuetype=get_data_from_layername)

        # Define how to process
        def process(result):
            if isinstance(result, Exception):
                popup_message(self, "Failed to merge the data:" + "\n\n" + str(result) )
            else:
                layerspane.add_layer(result, name="merged")
        self.runtool.set_finished_method(process)

class VectorOverlapSummaryWindow(Window):
    def __init__(self, master, layerspane, statusbar, **kwargs):
        # Make this class a subclass and add to it
        Window.__init__(self, master, **kwargs)

        # Create runtoolframe
        self.runtool = RunToolFrame(self)
        self.runtool.pack(fill="both", expand=True)
        self.runtool.assign_statusbar(statusbar)
        
        # Set the remaining options
        self.runtool.set_target_method("Calculating overlap summary on data...", vector.analyzer.overlap_summary)
        def get_data_from_layername(name):
            data = None
            for layeritem in layerspane:
                if layeritem.namelabel["text"] == name:
                    data = layeritem.renderlayer.data
                    break
            return data
        self.runtool.add_option_input(argname="groupbydata",
                              label="Group by data",
                              default="(Choose layer)",
                              choices=[layeritem.namelabel["text"] for layeritem in layerspane],
                              valuetype=get_data_from_layername)
        self.runtool.add_option_input(argname="valuedata",
                              label="Value data",
                              default="(Choose layer)",
                              choices=[layeritem.namelabel["text"] for layeritem in layerspane],
                              valuetype=get_data_from_layername)
        self.runtool.add_option_input(argname="fieldmapping",
                              label="Field mapping",
                              multi=True,
                              valuetype=eval)

        # Define how to process
        def process(result):
            if isinstance(result, Exception):
                popup_message(self, "Failed to calculate overlap summary on data:" + "\n\n" + str(result) )
            else:
                layerspane.add_layer(result, name="overlap summary")
        self.runtool.set_finished_method(process)
    
class RasterMosaicOptionWindow(Window):
    def __init__(self, master, layerspane, statusbar, **kwargs):
        # Make this class a subclass and add to it
        Window.__init__(self, master, **kwargs)

        # Create runtoolframe
        self.runtool = RunToolFrame(self)
        self.runtool.pack(fill="both", expand=True)
        self.runtool.assign_statusbar(statusbar)
        
        # Set the remaining options
        self.runtool.set_target_method("Mosaicking data...", raster.manager.mosaic)
        def get_data_from_layername(name):
            data = None
            for layeritem in layerspane:
                if layeritem.namelabel["text"] == name:
                    data = layeritem.renderlayer.data
                    break
            return data
        self.runtool.add_option_input(argname=None,
                              label="Layers to be mosaicked",
                              multi=True,
                              choices=[layeritem.namelabel["text"] for layeritem in layerspane],
                              valuetype=get_data_from_layername)

        # Define how to process
        def process(result):
            if isinstance(result, Exception):
                popup_message(self, "Failed to mosaick the data:" + "\n\n" + str(result) )
            else:
                layerspane.add_layer(result, name="mosaicked")
        self.runtool.set_finished_method(process)

class RasterZonalStatsOptionWindow(Window):
    def __init__(self, master, layerspane, statusbar, **kwargs):
        # Make this class a subclass and add to it
        Window.__init__(self, master, **kwargs)

        # Create runtoolframe
        self.runtool = RunToolFrame(self)
        self.runtool.pack(fill="both", expand=True)
        self.runtool.assign_statusbar(statusbar)
        
        # Set the remaining options
        self.runtool.set_target_method("Calculating zonal statistics on data...", raster.analyzer.zonal_statistics)
        def get_data_from_layername(name):
            data = None
            for layeritem in layerspane:
                if layeritem.namelabel["text"] == name:
                    data = layeritem.renderlayer.data
                    break
            return data
        self.runtool.add_option_input(argname="zonaldata",
                              label="Zonal data",
                              default="(Choose layer)",
                              choices=[layeritem.namelabel["text"] for layeritem in layerspane],
                              valuetype=get_data_from_layername)
        self.runtool.add_option_input(argname="valuedata",
                              label="Value data",
                              default="(Choose layer)",
                              choices=[layeritem.namelabel["text"] for layeritem in layerspane],
                              valuetype=get_data_from_layername)
        self.runtool.add_option_input(argname="zonalband",
                              label="Zonal band",
                              valuetype=int,
                              default=0)
        self.runtool.add_option_input(argname="valueband",
                              label="Value band",
                              valuetype=int,
                              default=0)
        self.runtool.add_option_input(argname="outstat",
                              label="Output Raster Statistic",
                              valuetype=str,
                              default="mean",
                              choices=["min","max","count","sum","mean","median","var","stddev"])

        # Define how to process
        def process(result):
            if isinstance(result, Exception):
                popup_message(self, "Failed to calculate zonal statistics on the data:" + "\n\n" + str(result) )
            else:
                zonesdict, outraster = result
                # add the resulting zonestatistics layer
                layerspane.add_layer(outraster, name="zonal statistic")
                # also view stats in window
                win = Window()
                textbox = tkst.ScrolledText(win)
                textbox.pack(fill="both", expand=True)
                textbox.insert(tk.END, "Zonal statistics detailed result:")
                textbox.insert(tk.END, "\n---------------------------------\n")
                for zone,stats in zonesdict.items():
                    statstext = "\n"+"Zone %i:"%zone
                    statstext += "\n\t" + "\n\t".join(["%s: %f"%(key,val) for key,val in stats.items()])
                    textbox.insert(tk.END, statstext)
        self.runtool.set_finished_method(process)



