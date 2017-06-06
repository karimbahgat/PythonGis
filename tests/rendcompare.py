
from time import time

# renderers
import PIL, PIL.Image, PIL.ImageDraw, PIL.ImagePath
import aggdraw
import cairo

class Aggrend:
    
    def setup_img(self, width, height):
        # setup
        self.img = PIL.Image.new('RGBA', (int(width), int(height)), "blue")
        self.drawer = aggdraw.Draw(self.img)
        #self.drawer.settransform([300,300])
        #self.drawer.settransform([360/float(width), 0, -180,
        #                          0, -180/float(height), 90])
        self.drawer.settransform((2.7777777777777777, 0.0, 500.0, 0.0, -2.7777777777777777, 250.0))
        #self.drawer.setantialias(False)
        self.brush = aggdraw.Brush("green")
        self.pen = aggdraw.Pen("black", 0.3)

    def setup_dib(self, width, height):
        # setup
        self.drawer = aggdraw.Dib('RGB', (int(width), int(height)), "blue")
        #self.drawer.settransform([300,300])
        #self.drawer.settransform([360/float(width), 0, -180,
        #                          0, -180/float(height), 90])
        self.drawer.settransform((2.7777777777777777, 0.0, 500.0, 0.0, -2.7777777777777777, 250.0))
        #self.drawer.setantialias(False)
        self.brush = aggdraw.Brush("green")
        self.pen = aggdraw.Pen("black", 0.3)

    def draw_path(self, polys):
        # draw
        path = aggdraw.Path()

        for poly in polys:
            exterior = poly[0]
            if len(poly) > 1:
                holes = poly[1:]
            else:
                holes = []
        
            def traverse_ring(coords):
                # begin
                coords = (point for point in coords)
                startx,starty = next(coords)
                path.moveto(startx, starty) 
                
                # connect to each successive point
                for nextx,nexty in coords:
                    path.lineto(nextx, nexty)
                path.close()

            # first exterior
            traverse_ring(exterior)

            # then holes
            for hole in holes:
                # !!! need to test for ring direction !!!
                hole = (point for point in hole)
                traverse_ring(hole)

        self.drawer.path((0,0), path, self.pen, self.brush)

    def draw_symbol(self, polys):
        # draw
        global svg
        svg = ""

        for poly in polys:
            exterior = poly[0]
            if len(poly) > 1:
                holes = poly[1:]
            else:
                holes = []
        
            def traverse_ring(coords):
                global svg
                # begin
                coords = (point for point in coords)
                startx,starty = next(coords)
                svg += " M%s,%s"%(startx, starty) 
                
                # connect to each successive point
                for nextx,nexty in coords:
                    svg += " L%s,%s"%(nextx, nexty)

            # first exterior
            traverse_ring(exterior)

            # then holes
            for hole in holes:
                # !!! need to test for ring direction !!!
                hole = (point for point in hole)
                traverse_ring(hole)

        self.drawer.symbol((0,0), aggdraw.Symbol(svg.strip()), self.pen, self.brush)

    def draw_polygon(self, polys):
        # draw
        for poly in polys:
            exterior = poly[0]
            flat = [xory for pt in exterior for xory in pt]

            # first exterior
            self.drawer.polygon(flat, self.pen, self.brush)

    def view(self):
        self.img.show()

    def test(self):
        # aggdraw img
        # aggdraw mode
        # aggdraw dib
        # aggdraw no antialias
        setups = {"img": lambda: self.setup_img(1000,500),
                  #"dib": lambda: self.setup_dib(1000,500),
                  }

        # aggdraw path
        # aggdraw symbol
        draws = {"path": lambda p: self.draw_path(p),
                 #"symbol": lambda p: self.draw_symbol(p),
                 "polygon": lambda p: self.draw_polygon(p),
                 }

        # aggdraw all at once

        # run
        for slab,setup in setups.items():
            setup()
            for dlab,draw in draws.items():
                t=time()
                for p in polys:
                    draw(p)
                #draw([extorhole for p in polys for extorhole in p])
                self.drawer.flush()
                print slab, dlab, time()-t
                #self.view()
        

class PILrend:
    
    def setup_img(self, width, height):
        # setup
        self.img = PIL.Image.new('RGBA', (int(width), int(height)), "blue")
        self.drawer = PIL.ImageDraw.Draw(self.img)
        #self.drawer.settransform([300,300])
        #self.drawer.settransform([360/float(width), 0, -180,
        #                          0, -180/float(height), 90])
        #self.drawer.settransform((2.7777777777777777, 0.0, 500.0, 0.0, -2.7777777777777777, 250.0))
        #self.drawer.setantialias(False)
        self.brush = "green"
        self.pen = "black"

    def draw_polygon(self, polys):
        # draw
        for poly in polys:
            exterior = poly[0]
            if len(poly) > 1:
                holes = poly[1:]
            else:
                holes = []

            # first exterior
            path = PIL.ImagePath.Path(exterior)
            path.transform((2.7777777777777777, 0.0, 500.0, 0.0, -2.7777777777777777, 250.0))
            path.compact(1)
            if len(path) > 1:
                self.drawer.polygon(path, self.brush, self.pen)
                self.drawer.line(path, self.pen, 1)

            # then holes
            for hole in holes:
                path = PIL.ImagePath.Path(hole)
                path.transform((2.7777777777777777, 0.0, 500.0, 0.0, -2.7777777777777777, 250.0))
                path.compact(1)
                if len(path) > 1:
                    self.drawer.polygon(path, (0,0,0,0), None)
                    self.drawer.line(path, self.pen, 1)

    def view(self):
        self.img.show()

    def test(self):
        # aggdraw img
        # aggdraw mode
        # aggdraw dib
        # aggdraw no antialias
        setups = {"img": lambda: self.setup_img(1000,500)
                  }

        # aggdraw path
        # aggdraw symbol
        draws = {"polygon": lambda p: self.draw_polygon(p),
                 }

        # aggdraw all at once

        # run
        for slab,setup in setups.items():
            setup()
            for dlab,draw in draws.items():
                t=time()
                for p in polys:
                    draw(p)
                #draw([extorhole for p in polys for extorhole in p])
                print slab, dlab, time()-t
                #self.view()


class Cairorend:
    
    def setup_img(self, width, height):
        # setup
        self.img = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.drawer = cairo.Context(self.img)
        self.drawer.translate(500, 250)
        self.drawer.scale(2.7777777, -2.7777777)
        self.brush = (0,1,0)
        self.pen = (0,0,0)

    def draw_path(self, polys):
        #define symbolics
        self.drawer.set_source_rgb(*self.pen) # Solid color
        self.drawer.set_line_width(0.3)
            
        # draw
        for poly in polys:
            exterior = poly[0]
            if len(poly) > 1:
                holes = poly[1:]
            else:
                holes = []

            # first exterior
            x,y = exterior[0]
            #x,y = self.drawer.device_to_user(x,y)
            self.drawer.move_to(x,y)
            for x,y in exterior[1:]:
                #x,y = self.drawer.device_to_user(x,y)
                self.drawer.line_to(x,y)
            self.drawer.close_path()
            self.drawer.stroke_preserve()
            self.drawer.set_source_rgb(*self.brush)
            self.drawer.fill()
            
            # then holes
            for hole in holes:
                x,y = hole[0]
                #x,y = self.drawer.device_to_user(x,y)
                self.drawer.move_to(x,y)
                for x,y in hole[1:]:
                    #x,y = self.drawer.device_to_user(x,y)
                    self.drawer.line_to(x,y)
                self.drawer.close_path()
                self.drawer.stroke_preserve()
                self.drawer.set_source_rgb(*self.brush)
                self.drawer.fill()
                
    def view(self):
        pass #self.img.write_to_png("testcairo.png")

    def test(self):
        # aggdraw img
        # aggdraw mode
        # aggdraw dib
        # aggdraw no antialias
        setups = {"img": lambda: self.setup_img(1000,500)
                  }

        # aggdraw path
        # aggdraw symbol
        draws = {"path": lambda p: self.draw_path(p),
                 }

        # aggdraw all at once

        # run
        for slab,setup in setups.items():
            setup()
            for dlab,draw in draws.items():
                t=time()
                for p in polys:
                    draw(p)
                #draw([extorhole for p in polys for extorhole in p])
                print slab, dlab, time()-t
                self.view()

    


# RUN

# data
import shapefile
reader = shapefile.Reader(r"C:\Users\kimo\Downloads\ne_10m_admin_1_states_provinces\ne_10m_admin_1_states_provinces.shp")
#reader = shapefile.Reader(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp")
shapes = [s.__geo_interface__ for s in reader.shapes()]
polys = [geoj["coordinates"] if geoj["type"]=="MultiPolygon" else [geoj["coordinates"]] for geoj in shapes]
#polys = [[extorhole for p in polys for extorhole in p]] # draws all as one big multipoly, but no apparent speed diff
print "loaded"

# test
print "AGG"
aggrend = Aggrend()
aggrend.test()
print "PIL"
pilrend = PILrend()
pilrend.test()
print "Cairo"
cairorend = Cairorend()
cairorend.test()


