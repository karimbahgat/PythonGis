#########################
#!/usr/bin/python
# -*- coding: utf-8 -*- 
# python version 2.6.5
author = "Karim Bahgat (PRIO)"
softwarename = "GED events aggregated to province-year"
versionnr = "0,11"


#########################
# INITIALIZING
#########################
print "initializing"
# Import main modules
import imp, csv, os, sys, time, pickle, traceback, difflib, datetime, codecs, operator, math, shutil, urllib, decimal, random
from math import *
import Tkinter
from Tkinter import *
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import cartopy
import cartopy.crs as carto
import shapely
from geovis import shapefile_fork as shapefile
import numpy as np

# Set up input dirs and vars
workspace = "\\".join(sys.argv[0].split("\\")[:-1])
scriptspace = r"C:\Users\BIGKIMO\Dropbox\Work\Research\Software\Various Python Libraries\custommodules" #workspace+"\\custommodules"
filespace = workspace #r"C:\Users\BIGKIMO\Desktop\PRIO work\GED\Data\GED_ADMIN"
outputspace = filespace
# Import custom modules
sys.path.append(scriptspace)
from tablereader import CreateReaderObject
from aggregator import CreateAggregator
from txt import txt
from report import Report
from shapebasics import CreateShapeTools




class ShapeSymbol:
    def init(self):
        self.fillcolor = "green"
        self.outlinecolor = "black"
        pass

    

class CreateMapEngine:
    def __init__(self, parentwidget, projection, mapdimensions=(8,4), resolution=100):
        # CREATE MAP ITSELF AT TOP LEFT OF PARENT WIDGET
        self.parentwidget = parentwidget
        projectiondefs = { "PlateCarree":carto.PlateCarree(),
                           "Mercator":carto.Mercator() }
        
        self.proj = projectiondefs[projection]
        self.mapframe = Figure(figsize=mapdimensions, dpi=resolution)
        self.ax = self.mapframe.add_axes([0.01, 0.01, 0.98, 0.98], projection=self.proj)
        self.ax.set_title(">>> Click To Insert Map Title <<<")
        self.ax.coastlines()
        self.ax.set_global()
        self.mapframe_tk_version = FigureCanvasTkAgg(self.mapframe, master=self.parentwidget)
        self.mapframe_tk_version.get_tk_widget().place(relx=0.2, rely=0, relwidth=0.8, relheight=0.95)    #.pack(side="top", fill="both", expand=1)
        self.mapframe_tk_version.show()
        # CREATE BOTTOM INFO AND COORDS BAR AT BOTTOM
        bottominfo = Frame(master=parentwidget)
        bottominfo.place(relx=0, rely=0.95, relwidth=1, relheight=0.05)
        self.coordsdisplay = Label(master=bottominfo, text="x,y", width=30)
        self.coordsdisplay.pack(side="right", anchor="e")
        self.zoomdisplay = Label(master=bottominfo, text="Showing "+str(100.0)+"% of full extent", width=30)
        self.zoomdisplay.pack(side="right", anchor="e")
        self.projectiondisplay = Label(master=bottominfo, text="Map projection: "+projection, width=30)
        self.projectiondisplay.pack(side="left", anchor="w")

        # CREATE LEFT SHAPEFILE VISUAL LAYER MANAGER LIST
        layersframe = Frame(master=parentwidget, bg="dark grey")
        layersframe.place(relx=0, rely=0, relwidth=0.2, relheight=0.95)
        layersframe_header = Label(master=layersframe, text="Shapefile Layers:", bg="black", fg="white", anchor="w")
        layersframe_header.place(relx=0.03, rely=0.01, relwidth=0.94, relheight=0.09, anchor="nw")
        self.layersview = Frame(master=layersframe, bg="white")
        self.layersview.place(relx=0.03, rely=0.1, relwidth=0.94, relheight=0.89)
        self.layerobjects = dict()

        # BIND INTERACTIVE EVENTS LIKE ZOOM, PAN, AND SELECT
        self.zoomtracker = 100
        self.clicktime = time.time()
        self.mousepressed = False
        self.mapframe.canvas.mpl_connect('button_press_event', self.MousePressed)
        self.mapframe.canvas.mpl_connect('button_release_event', self.MouseReleased)
        self.mapframe.canvas.mpl_connect('motion_notify_event', self.MouseMoving)

        # FINISHED BC ALL NEW WINDOWS HAVE BEEN PLACED WITHIN THE PARENTWIDGET, AND RETURN MAPENGINE OBJECT SO USER CAN USE OTHER FUNCTIONS SUCH AS CHANGE TITLE






    ### RENDERING
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



    ### INTERACTIVE
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
    def SelectShape(self):
        pass

            
