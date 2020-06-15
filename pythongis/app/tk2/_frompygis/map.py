# Import builtins
import time

# Import GUI libraries
import Tkinter as tk
from .. import icons

# Import GIS functionality
import pythongis as pg
from . import dispatch
from .popups import popup_message


# Import style
from . import theme
style_map_normal = {"bg": theme.color1}



# The Main Map

class MapView(tk.Canvas):
    def __init__(self, master, **kwargs):
        # get theme style
        style = style_map_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Canvas and add to it
        tk.Canvas.__init__(self, master, **style)

        # Other
        self.proj = kwargs.get("projection", "WGS84")
        self.statusbar = None
        self.mousepressed = False
        self.mouse_mode = "pan"
        self.zoomcenter = None
        self.zoomfactor = 1
        self.zoomdir = None
        self.last_zoomed = None

        # Assign a renderer just after startup, bc only then can one know the required window size
        def on_startup():
            # create renderer
            width, height = self.winfo_width(), self.winfo_height()
            self.renderer = pg.MapCanvas(self.layers, width, height)
            # link to self
            self.renderer.mapview = self
            # fill with blank image
            self.tkimg = self.renderer.get_tkimage()
            self.image_on_canvas = self.create_image(0, 0, anchor="nw", image=self.tkimg )

        self.after(10, on_startup)
        
        # Schedule resize map on window resize
        self.last_resized = None
        def resizing(event):
            # record resize time
            self.last_resized = time.time()
            # schedule to check if finished resizing after x millisecs
            self.after(300, process_if_finished)
        def process_if_finished():
            # only if x time since last resize event
            if time.time() - self.last_resized > 0.3:
                width, height = self.winfo_width(), self.winfo_height()
                self.renderer.resize(width, height)
                self.threaded_rendering()
        self.bind("<Configure>", resizing)
        
        # Bind interactive zoom events
        def doubleleft(event):
            self.zoomfactor += 1
            canvasx,canvasy = self.canvasx(event.x),self.canvasy(event.y)
            self.zoomcenter = self.renderer.pixel2coord(canvasx, canvasy)
            self.zoomdir = "in"
            # record zoom time
            self.last_zoomed = time.time()
            # schedule to check if finished zooming after x millisecs
            self.after(300, zoom_if_finished)
        def doubleright(event):
            self.zoomfactor += 1
            canvasx,canvasy = self.canvasx(event.x),self.canvasy(event.y)
            self.zoomcenter = self.renderer.pixel2coord(canvasx, canvasy)
            self.zoomdir = "out"
            # record zoom time
            self.last_zoomed = time.time()
            # schedule to check if finished zooming after x millisecs
            self.after(300, zoom_if_finished)
        def zoom_if_finished():
            if time.time() - self.last_zoomed >= 0.3:
                if self.zoomdir == "out":
                    self.zoomfactor *= -1
                self.renderer.zoom_factor(self.zoomfactor, center=self.zoomcenter)
                self.threaded_rendering()
                # reset zoomfactor
                self.zoomfactor = 1
                self.last_zoomed = None
        self.bind("<Double-Button-1>", doubleleft)
        self.bind("<Double-Button-3>", doubleright)

        # bind interactive pan and rectangle-zoom events
        def mousepressed(event):
            if self.last_zoomed: return
            self.mousepressed = True
            self.startxy = self.canvasx(event.x), self.canvasy(event.y)
            if self.mouse_mode == "zoom":
                startx,starty = self.startxy
                self.rect = self.create_rectangle(startx, starty, startx+1, starty+1, fill=None)
        def mousemoving(event):
            if self.statusbar:
                # mouse coords
                mouse = self.canvasx(event.x), self.canvasy(event.y)
                xcoord,ycoord = self.renderer.pixel2coord(*mouse)
                self.statusbar.mouse.set_text("%3.8f , %3.8f" %(xcoord,ycoord) )
            if self.mouse_mode == "pan":
                if self.mousepressed:
                    startx,starty = self.startxy
                    curx,cury = self.canvasx(event.x), self.canvasy(event.y)
                    xmoved = curx - startx
                    ymoved = cury - starty
                    self.coords(self.image_on_canvas, xmoved, ymoved) # offset the image rendering
            elif self.mouse_mode == "zoom":
                curx,cury = self.canvasx(event.x), self.canvasy(event.y)
                self.coords(self.zoomicon_on_canvas, curx, cury)
                if self.mousepressed:
                    startx,starty = self.startxy
                    self.coords(self.rect, startx, starty, curx, cury)
        def mousereleased(event):
            if self.last_zoomed: return
            self.mousepressed = False
            if self.mouse_mode == "pan":
                startx,starty = self.startxy
                curx,cury = self.canvasx(event.x), self.canvasy(event.y)
                xmoved = int(curx - startx)
                ymoved = int(cury - starty)
                if xmoved or ymoved:
                    self.renderer.offset(xmoved, ymoved) # offset image rendering
                    self.threaded_rendering()
            elif self.mouse_mode == "zoom":
                startx,starty = self.startxy
                curx,cury = self.canvasx(event.x), self.canvasy(event.y)
                self.coords(self.rect, startx, starty, curx, cury)
                # disactivate rectangle selector
                self.delete(self.rect)
                self.event_generate("<Leave>") # fake a mouseleave event to destroy icon
                self.mouse_mode = "pan"
                # make the zoom
                startx,starty = self.renderer.drawer.pixel2coord(startx,starty)
                curx,cury = self.renderer.drawer.pixel2coord(curx,cury)
                bbox = [startx, starty, curx, cury]
                #self.rough_zoom_bbox(bbox)
                self.renderer.zoom_bbox(*bbox)
                self.threaded_rendering()
        def mouseenter(event):
            if self.mouse_mode == "zoom":
                # replace mouse with zoomicon
                self.zoomicon_tk = icons.get("zoom_rect.png").resize(30, 30).get_tkimage()
                self.zoomicon_on_canvas = self.create_image(event.x, event.y, anchor="center", image=self.zoomicon_tk )
                self.config(cursor="none")
        def mouseleave(event):
            if self.mouse_mode == "zoom":
                # back to normal mouse
                self.delete(self.zoomicon_on_canvas)
                self.config(cursor="arrow")
        def cancel(event):
            if self.mouse_mode == "zoom":
                self.event_generate("<Leave>") # fake a mouseleave event to destroy icon
                self.mouse_mode = "pan"
                if self.mousepressed:
                    self.delete(self.rect)

        # bind them
        self.bind("<Button-1>", mousepressed, "+")
        self.bind("<Motion>", mousemoving)
        self.bind("<ButtonRelease-1>", mousereleased, "+")
        self.bind("<Enter>", mouseenter)
        self.bind("<Leave>", mouseleave)
        self.winfo_toplevel().bind("<Escape>", cancel)

    def zoom_global(self):
        layerbboxes = (layer.data.bbox for layer in self.renderer.layers)
        xmins,ymins,xmaxs,ymaxs = zip(*layerbboxes)
        globalbbox = [min(xmins), min(ymins), max(xmaxs), max(ymaxs)]
        #self.rough_zoom_bbox(globalbbox)
        self.renderer.zoom_bbox(*globalbbox)
        self.threaded_rendering()

    def zoom_rect(self):
        self.mouse_mode = "zoom"
        self.event_generate("<Enter>")

    def assign_layergroup(self, layergroup):
        self.layers = layergroup

    def assign_statusbar(self, statusbar):
        statusbar.mapview = self
        self.statusbar = statusbar

##    def rough_zoom_bbox(self, zoom_bbox):
##
##        # crop current image if necessary
##        self.renderer.drawer.crop(*zoom_bbox)
##        
##        # resize
##        self.renderer.drawer.resize(int(self.winfo_width()), int(self.winfo_height()) )
##        
##        # update image on canvas
##        self.tkimg = self.renderer.get_tkimage()
##        self.itemconfig(self.image_on_canvas, image=self.tkimg )

    def await_draw_point(self):
        def place_button(event):
            self.create_rectangle(event.x, event.y, event.x+10, event.y+10)
            #self.unbind(bindid)
        bindid = self.bind("<Button-3>", place_button, "+")

    def await_draw_lines(self):
        coords = []
        vertexids = []
        lineids = []
        mousevertex = self.create_rectangle(0-5, 0-5, 0+5, 0+5)
        mouseline = self.create_line(0-5, 0-5, 0+5, 0+5, dash=(3,3))

        def add_vertex(event):
            # draw line
            if len(coords) >= 1:
                lineid = self.create_line(coords[-1][0], coords[-1][1], event.x, event.y)
                lineids.append(lineid)
                
            # draw point
            coords.append((event.x, event.y))
            vertexid = self.create_rectangle(event.x-5, event.y-5, event.x+5, event.y+5)
            vertexids.append(vertexid)

        def mouse_moves(event):
            self.coords(mousevertex, event.x-5, event.y-5, event.x+5, event.y+5)
            if len(coords) >= 1:
                self.coords(mouseline, coords[-1][0], coords[-1][1], event.x, event.y)

        avid = self.bind("<Button-1>", add_vertex, "+")
        mmid = self.bind("<Motion>", mouse_moves, "+")

        def undo(event):
            del coords[-1]
            self.delete(vertexids.pop(-1))
            self.delete(lineids.pop(-1))
        
        unid = self.bind_all("<BackSpace>", undo, "+")

        def finish(event):
            self.delete(mousevertex)
            self.delete(mouseline)
            self.unbind("<Button-1>", avid)
            self.unbind("<Motion>", mmid)
            self.unbind("<BackSpace>", undo)
            
        self.bind("<Button-3>", finish)

    def threaded_rendering(self):
        # perform render/zoom in separate thread
        self.statusbar.task.start("Rendering layers...")
        pending = dispatch.request_results(self.renderer.render_all)

        def finish(result):
            if isinstance(result, Exception):
                popup_message(self, "Rendering error: " + str(result) )
            else:
                # update renderings
                self.coords(self.image_on_canvas, 0, 0) # always reanchor rendered image nw at 0,0 in case of panning
                self.update_image()
                # display zoom scale
                self.statusbar.zoom.set_text("1:"+str(self.renderer.drawer.coordspace_units) )
            self.statusbar.task.stop()
            
        dispatch.after_completion(self, pending, finish)

    def update_image(self):
        self.tkimg = self.renderer.get_tkimage()
        self.itemconfig(self.image_on_canvas, image=self.tkimg )





