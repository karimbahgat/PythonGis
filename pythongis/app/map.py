# Import builtins
import time
import Tkinter as tk
import tk2
import pythongis as pg



# The Main Map

class MapView(tk.Canvas):
    def __init__(self, master, renderer, **kwargs):        
        # Make this class a subclass of tk.Canvas and add to it
        tk.Canvas.__init__(self, master, **kwargs)
        self.renderer = renderer
        self.controls = []

        # Other
        self.onstart = None
        self.onsuccess = None
        self.onfinish = None
        self.onmousemove = None
        
        self.mousepressed = False
        self.mouse_mode = "pan"
        self.zoomcenter = None
        self.zoomfactor = 1
        self.zoomdir = None
        self.last_zoomed = None

        # Assign a renderer just after startup, because only then can one know the required window size
        def on_startup():
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
            self.after(300, lambda: process_if_finished(event))
            
        def process_if_finished(event):
            # only if x time since last resize event
            if time.time() - self.last_resized > 0.3:
                self.last_resized = time.time()
                width, height = event.width, event.height #self.winfo_width(), self.winfo_height()
                self.renderer.resize(width, height)
                #self.renderer.width = width
                #self.renderer.height = height
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

        def mousewheel(event):
            # FIX: since we bind to all, event coordinates are captured by root
            # so it seems these are not what canvasx/y expect, leading to wacky zooms... 
            d = event.delta
            #print event.x,event.y
            #event.x,event.y = self.winfo_pointerxy()
            #print event.x,event.y
            if d < 0:
                doubleright(event)
            else:
                doubleleft(event)

        def zoom_if_finished():
            if time.time() - self.last_zoomed >= 0.3:
                if self.zoomdir == "out":
                    self.renderer.zoom_out(self.zoomfactor, center=self.zoomcenter)
                else:
                    self.renderer.zoom_in(self.zoomfactor, center=self.zoomcenter)
                self.threaded_rendering()
                # reset zoomfactor
                self.zoomfactor = 1
                self.last_zoomed = None

        self.bind("<Double-Button-1>", doubleleft)
        self.bind("<Double-Button-3>", doubleright)
        # Warning: had to bind to all, since wasn't firing on just the canvas,
        # so mousewheel will trigger zoom even when pointer outside the map
        #self.bind_all("<MouseWheel>", mousewheel)
        #self.bind_all("<Button-4>", mousewheel)
        #self.bind_all("<Button-5>", mousewheel)

        # bind interactive pan and rectangle-zoom events

        def mousepressed(event):
            if self.last_zoomed: return
            self.mousepressed = True
            self.startxy = self.canvasx(event.x), self.canvasy(event.y)
            if self.mouse_mode == "zoom":
                startx,starty = self.startxy
                self.rect = self.create_rectangle(startx, starty, startx+1, starty+1, fill=None)

        def mousemoving(event):
            if self.onmousemove:
                # mouse coords
                self.onmousemove(event)
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
                    # offset image rendering
                    self.renderer.offset(xmoved, ymoved) 
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
                self.zoomicon_tk = icons.get("zoom_rect.png", width=30, height=30)
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

    def add_control(self, control):
        control.mapview = self
        self.controls.append(control)

    def zoom_global(self):
        layerbboxes = (layer.bbox for layer in self.renderer.layers)
        xmins,ymins,xmaxs,ymaxs = zip(*layerbboxes)
        globalbbox = [min(xmins), min(ymins), max(xmaxs), max(ymaxs)]
        self.renderer.zoom_bbox(*globalbbox)
        self.threaded_rendering()

    def zoom_rect(self):
        self.mouse_mode = "zoom"
        self.event_generate("<Enter>")

    def zoom_bbox(self, bbox):
        self.renderer.zoom_bbox(*bbox)
        self.threaded_rendering()

    def mouse2coords(self, x, y):
        px,py = self.canvasx(x), self.canvasy(y)
        x,y = self.renderer.pixel2coord(px, py)
        return x,y

    def threaded_rendering(self):
        # perform render/zoom in separate thread
        if self.onstart:
            self.onstart()
        print "rendering thread..."
        pending = self.master.new_thread(self.renderer.render_all)

        def finish(result):
            if isinstance(result, Exception):
                tk2.messagebox.showerror(self, "Rendering error: " + str(result) )
            else:
                # update renderings
                self.coords(self.image_on_canvas, 0, 0) # always reanchor rendered image nw at 0,0 in case of panning
                self.update_image()
                # display zoom scale
                if self.onsuccess:
                    self.onsuccess()
            # stop progbar
            if self.onfinish:
                self.onfinish()
            
        self.master.process_thread(pending, finish)

    def update_image(self):
        self.tkimg = self.renderer.get_tkimage()
        self.itemconfig(self.image_on_canvas, image=self.tkimg )

    def zoom_in(self):
        self.zoomfactor += 1
        self.zoomcenter = None
        self.zoomdir = "in"
        # record zoom time
        self.last_zoomed = time.time()
        # schedule to check if finished zooming after x millisecs
        self.after(300, self.zoom_if_finished)

    def zoom_out(self):
        self.zoomfactor += 1
        self.zoomcenter = None
        self.zoomdir = "out"
        # record zoom time
        self.last_zoomed = time.time()
        # schedule to check if finished zooming after x millisecs
        self.after(300, self.zoom_if_finished)

    def zoom_if_finished(self):
        if time.time() - self.last_zoomed >= 0.3:
            if self.zoomdir == "out":
                self.renderer.zoom_out(self.zoomfactor)
            else:
                self.renderer.zoom_in(self.zoomfactor)
            self.threaded_rendering()
            # reset zoomfactor
            self.zoomfactor = 1
            self.last_zoomed = None





