
#from ._thirdparty import pyagg
from . import raster
import random
import pyagg
import PIL, PIL.Image, PIL.ImageTk



class MapCanvas:
    def __init__(self, layers, width, height, background=None, *args, **kwargs):

        # remember and be remembered by the layergroup
        self.layers = layers
        layers.connected_maps.append(self)

        # create the drawer with a default unprojected lat-long coordinate system
        self.drawer = pyagg.Canvas(width, height, background)
        self.drawer.geographic_space()

        self.img = self.drawer.get_image()

    # Map canvas alterations

    def offset(self, xmove, ymove):
        self.drawer.move(xmove, ymove)

    def resize(self, width, height):
        self.drawer.resize(width, height, lock_ratio=True)
        self.img = self.drawer.get_image()

    # Zooming

    def zoom_bbox(self, xmin, ymin, xmax, ymax):
        self.drawer.zoom_bbox(xmin, ymin, xmax, ymax)

    def zoom_factor(self, factor, center=None):
        self.drawer.zoom_factor(factor, center=center)

    def zoom_units(self, units, center=None):
        self.drawer.zoom_units(units, center=center)

    def pixel2coord(self, x, y):
        return self.drawer.pixel2coord(x, y)

    # Drawing

    def render_one(self, layer):
        if layer.visible:
            layer.render(width=self.drawer.width,
                         height=self.drawer.height,
                         coordspace_bbox=self.drawer.coordspace_bbox)
            self.update_draworder()

    def render_all(self):
        for layer in self.layers:
            if layer.visible:
                layer.render(width=self.drawer.width,
                             height=self.drawer.height,
                             coordspace_bbox=self.drawer.coordspace_bbox)
        self.update_draworder()

    def update_draworder(self):
        self.drawer.clear()
        for layer in self.layers:
            if layer.visible:
##                if layer.data.bbox != self.drawer.coordspace_bbox:
##                    layer.render(width=self.drawer.width,
##                                height=self.drawer.height,
##                                coordspace_bbox=self.drawer.coordspace_bbox)
                self.drawer.paste(layer.img)
        self.img = self.drawer.get_image()

    def get_tkimage(self):
        # Special image format needed by Tkinter to display it in te GUI
        return self.drawer.get_tkimage()

    def view(self):
        """Opens and views the image in a Tkinter window"""
        import Tkinter as tk
        win = tk.Tk()
        label = tk.Label(win)
        label.img = label["image"] = self.get_tkimage()
        label.pack(fill="both", expand=True)
        win.mainloop()

        


class LayerGroup:
    def __init__(self):
        self.layers = list()
        self.connected_maps = list()

    def __iter__(self):
        for layer in self.layers:
            yield layer

    def add_layer(self, layer):
        self.layers.append(layer)

    def move_layer(self, from_pos, to_pos):
        layer = self.layers.pop(from_pos)
        self.layers.insert(to_pos, layer)

    def remove_layer(self, position):
        self.layers.pop(position)

    def get_position(self, layer):
        return self.layers.index(layer)




class VectorLayer:
    def __init__(self, data, **options):
        
        self.data = data
        self.visible = True
        self.img = None
        
        # set random style color
        rand = random.randrange
        randomcolor = (rand(255), rand(255), rand(255), 255)
        firstfeature = next(self.data.__iter__())
        if "Line" in firstfeature.geometry["type"]:
            self.styleoptions = {"outlinecolor": randomcolor}
        else:
            self.styleoptions = {"fillcolor": randomcolor}
            
        # override default if any manually specified styleoptions
        self.styleoptions.update(options)

        # test projection # ONLY TESTING, REMEMBER TO COMMENT OUT
##        import pyproj
##        wgs84 = pyproj.Proj("+init=EPSG:4326")
##        fromspace = pyproj.Proj("+proj=ortho +lat_0=15 +lon_0=0 +x_0=0 +y_0=0 +a=6370997 +b=6370997 +units=m +no_defs")
##        #fromspace = pyproj.Proj("+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs ")
##        #fromspace = pyproj.Proj("+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
##
##        print self.data.bbox
##        for feat in self.data:
##            if "Polygon" in feat.geometry["type"]:
##                if "Multi" in feat.geometry["type"]:
##                    newmulticoords = []
##                    for multi in feat.geometry["coordinates"]:
##                        exterior = multi[0]
##                        xs,ys = zip(*exterior)
##                        xs,ys = pyproj.transform(wgs84, fromspace, xs, ys)
##                        newcoords = [[xy for xy in zip(xs,ys) if float("inf") not in xy]]
##                        if newcoords != [[]]:
##                            newmulticoords.append(newcoords)
##                    if newmulticoords != []:
##                        feat.geometry["coordinates"] = newmulticoords
##                        del feat.geometry["bbox"]
##                        feat._cached_bbox = None
##                else:
##                    exterior = feat.geometry["coordinates"][0]
##                    xs,ys = zip(*exterior)
##                    xs,ys = pyproj.transform(wgs84, fromspace, xs, ys)
##                    newcoords = [[xy for xy in zip(xs,ys) if float("inf") not in xy]]
##                    if newcoords != [[]]:
##                        feat.geometry["coordinates"] = newcoords
##                        del feat.geometry["bbox"]
##                        feat._cached_bbox = None
##            elif "LineString" in feat.geometry["type"]:
##                if "Multi" in feat.geometry["type"]:
##                    newmulticoords = []
##                    for multi in feat.geometry["coordinates"]:
##                        xs,ys = zip(*multi)
##                        xs,ys = pyproj.transform(wgs84, fromspace, xs, ys)
##                        newcoords = [xy for xy in zip(xs,ys) if float("inf") not in xy]
##                        if newcoords != []:
##                            newmulticoords.append(newcoords)
##                    if newmulticoords != []:
##                        feat.geometry["coordinates"] = newmulticoords
##                        del feat.geometry["bbox"]
##                        feat._cached_bbox = None
##                else:
##                    xs,ys = zip(*feat.geometry["coordinates"])
##                    xs,ys = pyproj.transform(wgs84, fromspace, xs, ys)
##                    newcoords = [xy for xy in zip(xs,ys) if float("inf") not in xy]
##                    if newcoords != []:
##                        feat.geometry["coordinates"] = newcoords
##                        del feat.geometry["bbox"]
##                        feat._cached_bbox = None
##            elif "Point" in feat.geometry["type"]:
##                if "Multi" in feat.geometry["type"]:
##                    continue
##                    print 31231
##                    xs,ys = zip(*feat.geometry["coordinates"])
##                    xs,ys = pyproj.transform(wgs84, fromspace, xs, ys)
##                    newcoords = [xy for xy in zip(xs,ys) if float("inf") not in xy]
##                    if newcoords != []:
##                        feat.geometry["coordinates"] = newcoords
##                        feat._cached_bbox = None
##                else:
##                    x,y = feat.geometry["coordinates"]
##                    xs,ys = pyproj.transform(wgs84, fromspace, (x,1), (y,1))
##                    x,y = xs[0],ys[0]
##                    if float("inf") not in (x,y): 
##                        feat.geometry["coordinates"] = [x,y]
##                        feat._cached_bbox = [x,y,x,y]
##
##        print self.data.bbox 

    def render(self, width, height, coordspace_bbox):
        drawer = pyagg.Canvas(width, height, background=None)
        drawer.custom_space(*coordspace_bbox)
        # get features based on spatial index, for better speeds when zooming
        if not hasattr(self.data, "spindex"):
            self.data.create_spatial_index()
        spindex_features = self.data.quick_overlap(coordspace_bbox)
        # draw each as geojson
        for feat in spindex_features:
            drawer.draw_geojson(feat.geometry, **self.styleoptions)
        self.img = drawer.get_image()



        
class RasterLayer:
    def __init__(self, data, **options):
        self.data = data
        self.styleoptions = dict(**options)
        self.visible = True
        self.img = None

        # test projection # ONLY TESTING, REMEMBER TO COMMENT OUT
##        import pyproj
##        # setup projections
##        fromproj = pyproj.Proj("+init=EPSG:4326")
##        toproj = pyproj.Proj("+proj=ortho +lat_0=15 +lon_0=0 +x_0=0 +y_0=0 +a=6370997 +b=6370997 +units=m +no_defs")
##        toproj = pyproj.Proj("+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs ")
##        #toproj = pyproj.Proj("+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
##        
##        # calculate bounding box of target projection
##        import itertools
##        def get_proj_bounds():
##            xs,ys = itertools.izip(*(self.data.cell_to_geo(cell.x, cell.y) for cell in self.data.grids[0]))
##            txs,tys = pyproj.transform(fromproj, toproj, xs, ys)
##            # remove infinitys
##            inf = float("inf")
##            txys = itertools.izip(txs, tys)
##            txs_noinf,tys_noinf = itertools.izip(*[txy for txy in txys if inf not in txy])
##            #txs_noinf = [tx for tx in txs if tx != inf]
##            #tys_noinf = [ty for ty in tys if ty != inf]
##            return [min(txs_noinf), min(tys_noinf), max(txs_noinf), max(tys_noinf)]
##
##        dst_rasterwidth,dst_rasterheight = self.data.width, self.data.height
##        dst_bbox = get_proj_bounds()
##        projw,projh = dst_bbox[2]-dst_bbox[0], dst_bbox[3]-dst_bbox[1]
##        cellw,cellh = projw/float(dst_rasterwidth), projh/float(dst_rasterheight)
##
##        print "setup complete"
##        print "raster dims",dst_rasterwidth,dst_rasterheight
##        print "raster bbox",dst_bbox
##        print "cell dims",cellw,cellh
##
##        # backward transform target projection to source proj
##        # starting at min destination bbox, and increment with cellsize (instead of incr pixels and having to transform which is unknown)
##        def dest_coords_gen():
##            dst_y = dst_bbox[1]
##            while dst_y < projh:
##                dst_x = dst_bbox[0]
##                while dst_x < projw:
##                    yield dst_x, dst_y
##                    dst_x += cellw
##                dst_y += cellh
##
####        print dest_coords_gen()
####        xs,ys = itertools.izip(*dest_coords_gen())
####
####        def get_backward_transform_coords(xs,ys):
####            txs,tys = pyproj.transform(toproj, fromproj, xs, ys)
####            return txs,tys
####        
####        txs,tys = get_backward_transform_coords(xs,ys)
####        print "transformed"
####
####        # finally, loop and write values, row by row
####        def grouper(iterable, n, fillvalue=None):
####            args = [iter(iterable)] * n
####            return itertools.izip_longest(fillvalue=fillvalue, *args)
####
####        xs,ys = itertools.izip(*dest_coords_gen())
####        xys = itertools.izip(xs, ys)
####        txys = itertools.izip(txs, tys)
####        xys_dst_src_mapping = itertools.izip(xys, txys)
####        rows = grouper(xys_dst_src_mapping, dst_rasterwidth)
####
####        print "mapped and grouped"
##
##        xs,ys = itertools.izip(*dest_coords_gen())
##        txs,tys = pyproj.transform(toproj, fromproj, xs, ys)
##        txys = (txy for txy in itertools.izip(txs,tys))
##        
##        testimg = PIL.Image.new("RGBA", (dst_rasterwidth,dst_rasterheight))
##        quads = []
##        dst_y = dst_bbox[1]
##        row = 0
##        while dst_y < projh:
##            print row
##            dst_x = dst_bbox[0]
##            col = 0
##            while dst_x < projw:
##                #print dst_x, dst_y
##                
####        for ri,row in enumerate(rows):
####            print ri
####            for ci,mapp in enumerate(row):
####                if not mapp: continue
####                xy,txy = mapp
##                #txy = pyproj.transform(toproj, fromproj, dst_x, dst_y)
##                txy = next(txys)
##                #print txy
##                try:
##                    cellpos = self.data.geo_to_cell(*txy)
##                    #q1 = [cellpos[0],cellpos[1],cellpos[0],cellpos[1]+1,
##                    #      cellpos[0]+1,cellpos[1]+1,cellpos[0]+1,cellpos[1]]
##                    #q2 = [col,row,col,row+1,
##                    #      col+1,row+1,col+1,row]
##                    #print q1,q2
##                    #quads.append((q1,q2))
##                    value = self.data.grids[0].get(*cellpos).value
##                    #print value,ci,ri
##                    #if value != 255:
##                    #    pass #print xy,txy
##                    #if value: print dst_px, value
##                    testimg.putpixel((col,row), value)
##                    #self.data.grids[0].set(col, row, value)
##                    #if value != 255:
##                    #    pass #print "-->-->", col,row, value
##                except Exception as err:
##                    #print err, txy, self.data.bbox
##                    pass
##                dst_x += cellw
##                col += 1
##            dst_y += cellh
##            row += 1
##        testimg.show()
##        print "done"
##        #img = self.data.grids[0].img.transform((self.data.width,self.data.height),
##        #                                        PIL.Image.MESH, quads)
##        #img.show()
        

##        # Sort of working, best one yet, but still unfinished
##        import pyproj
##        # setup projections
##        wgs84 = pyproj.Proj("+init=EPSG:4326")
##        fromspace = pyproj.Proj("+proj=ortho +lat_0=15 +lon_0=0 +x_0=0 +y_0=0 +a=6370997 +b=6370997 +units=m +no_defs")
##        fromspace = pyproj.Proj("+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs ")
##        fromspace = pyproj.Proj("+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
##        def make_lin_transf(src_bbox, dst_bbox):
##            # see https://bitbucket.org/olt/mapproxy/src/68a96f6effe091566f00d5575d9c7122f417837b/mapproxy/core/image.py?at=default
##            return lambda (x,y): (dst_bbox[0] + (x - src_bbox[0]) *
##                               (dst_bbox[2]-dst_bbox[0]) / (src_bbox[2] - src_bbox[0]),
##                               dst_bbox[1] + (src_bbox[3] - y) * 
##                               (dst_bbox[3]-dst_bbox[1]) / (src_bbox[3] - src_bbox[1]))
##        src_quad = (0,0,self.data.width, self.data.height)
##        src_bbox = self.data.bbox
##        #src_bbox = min(self.data.bbox[::2]),min(self.data.bbox[1::2]),max(self.data.bbox[::2]),max(self.data.bbox[1::2])
##        dst_quad = tuple(src_quad)
##        dst_bbox = [xory for xy in pyproj.transform(wgs84, fromspace, self.data.bbox[::2], self.data.bbox[1::2]) for xory in xy]
##        #dst_bbox = min(dst_bbox[::2]),min(dst_bbox[1::2]),max(dst_bbox[::2]),max(dst_bbox[1::2])
##        dst_bbox = [-20037508.3428, -15496570.7397, 20037508.3428, 18764656.2314]
##        print src_bbox
##        print dst_bbox
##        to_src_px = make_lin_transf(src_bbox, src_quad)
##        to_dst_w = make_lin_transf(dst_quad, dst_bbox)
##        print to_src_px
##        print to_dst_w
##        def dst_to_src(dst_px):
##            #print dst_px
##            dst_w = to_dst_w(dst_px)
##            #print "-->",dst_w
##            src_w = pyproj.transform(fromspace, wgs84, dst_w[1], dst_w[0])
##            src_px = to_src_px(src_w)
##            return src_px
##        newgrid = self.data.grids[0].copy()
##        gridget = self.data.grids[0].get
##        for cell in newgrid:
##            dst_px = cell.x, cell.y
##            #val = gridget(*dst_px).value
##            #if val: print dst_px,val
##            #continue
##            try:
##                src_px = dst_to_src(dst_px)
##                #if 60 == int(round(src_px[0])) or 60 == int(round(src_px[1])):
##                    #print src_px
##                value = gridget(int(round(src_px[0])), int(round(src_px[1]))).value
##                #if value: print dst_px, value
##                newgrid.set(dst_px[0], dst_px[1], value)
##                #print "-->-->", src_px, value
##            except Exception as err: pass #print err
##        newgrid.img.show()
##        print "done"

        
##        # set pixel bounds and coord bboxes
##        src_quad = (0,0,self.data.width, self.data.height)
##        src_bbox = self.data.bbox
##        # for destination, need to transform all cell coords (bc projection can twist and shape in many ways)
##        # ...then find the bbox of all the transformed cell coords
##        dst_quad = tuple(src_quad)
##        xs,ys = zip(*(self.data.cell_to_geo(cell.x, cell.y) for cell in self.data.grids[0]))
##        txs,tys = pyproj.transform(wgs84, fromspace, xs, ys)
##        #xs = [self.data.cell_to_geo(x, 0)[0] for x in range(self.data.width)]
##        #ys = [self.data.cell_to_geo(0, y)[1] for y in range(self.data.height)]
##        #txs,_ = pyproj.transform(wgs84, fromspace, xs, [0 for _ in range(len(xs))])
##        #_,tys = pyproj.transform(wgs84, fromspace, [0 for _ in range(len(ys))], ys)
##        # remove infinitys
##        inf = float("inf")
##        txys = zip(txs, tys)
##        txs_noinf = [tx for tx in txs if tx != inf]
##        tys_noinf = [ty for ty in tys if ty != inf]
##        dst_bbox = [min(txs_noinf), min(tys_noinf), max(txs_noinf), max(tys_noinf)]
##        print src_bbox
##        print dst_bbox
##
##        x1,y1,x2,y2 = dst_bbox
##        xmin,ymin,xmax,ymax = min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)
##        dst_bbox_width = float(xmax-xmin)
##        dst_bbox_height = float(ymax-ymin)
##        dst_bbox_xoff = xmin
##        dst_bbox_yoff = ymin
##        
##        x1,y1,x2,y2 = src_bbox
##        xmin,ymin,xmax,ymax = min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)
##        src_bbox_width = float(xmax-xmin)
##        src_bbox_height = float(ymax-ymin)
##        src_bbox_xoff = xmin
##        src_bbox_yoff = ymin
##        
##        #x1,y1,x2,y2 = src_quad
##        #xmin,ymin,xmax,ymax = min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)
##        #src_quad_width = float(xmax-xmin)
##        #src_quad_height = float(ymax-ymin)       
##        def destination2source(x,y):
##            xratio = (x-dst_bbox_xoff)/dst_bbox_width
##            yratio = (y-dst_bbox_yoff)/dst_bbox_height
##            #print "xy", x,y
##            #print "dims", dst_bbox_width, dst_bbox_height
##            #print "offs", dst_bbox_xoff, dst_bbox_yoff
##            #print "ratios", xratio, yratio
##            #print "values", src_bbox_width*xratio + src_bbox_xoff, src_bbox_height*yratio + src_bbox_yoff
##            #return int(round(src_quad_width*xratio)), int(round(src_quad_height*yratio))
##            return src_bbox_width*xratio + src_bbox_xoff, src_bbox_height*yratio + src_bbox_yoff
##
##            # see https://bitbucket.org/olt/mapproxy/src/68a96f6effe091566f00d5575d9c7122f417837b/mapproxy/core/image.py?at=default
##            #return  (dst_bbox[0] + (x - src_bbox[0]) *
##            #           (dst_bbox[2]-dst_bbox[0]) / (src_bbox[2] - src_bbox[0]),
##            #           dst_bbox[1] + (src_bbox[3] - y) * 
##            #           (dst_bbox[3]-dst_bbox[1]) / (src_bbox[3] - src_bbox[1]))
##
##        geo_to_cell = self.data.geo_to_cell
##        print "1",self.data.width, len(txs)
##        print "2",self.data.height, len(tys)
##        print "3",len(xs),len(ys)
##
##        import itertools
##        def grouper(iterable, n, fillvalue=None):
##            # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
##            args = [iter(iterable)] * n
##            return itertools.izip_longest(fillvalue=fillvalue, *args)
##        #txys = itertools.izip(txs,tys)
##        txys_rows = grouper(txys, self.data.width)
##        #newimg = PIL.Image.new("RGB",(self.data.width,self.data.height))
##        #aggimg = pyagg.Canvas(self.data.width, self.data.height)
##        #aggimg.custom_space(*dst_bbox)
##        for grid in self.data:
##            print grid
##            gridget = grid.get
##            gridset = grid.set
##            for row,xysrow in enumerate(txys_rows):
##                print row
##                for col,(tx,ty) in enumerate(xysrow):
##                    if inf in (tx,ty): continue
##                    #print tx,ty
##                    src_x,src_y = destination2source(tx, ty)
##                    #print x,y
##                    #print tx,ty
##                    #print src_x,src_y
##                    #if not (xmin < src_x < xmax): continue
##                    #if not (ymin < src_y < ymax): continue
##                    #print src_x,src_y
##                    cellx,celly = geo_to_cell(src_x, src_y)
##                    #cellx,celly = aggimg.coord2pixel(tx,ty)
##                    #print cellx,celly
##                    #print col,row,cellx,celly
##                    try:
##                        #print x,y
##                        #print tx,ty
##                        #print src_x,src_y
##                        src_value = gridget(cellx,celly).value
##                        #if src_value != 0:
##                        #    print (src_x,src_y,col,row,src_value)
##                        gridset(col, row, src_value)
##                        #newimg.putpixel((col,row), src_value)
##                        #print "set", gridget(col,row)
##                        # random note: fromcell --> togeo --> totransfgeo --?-- totransfcell?
##                    except Exception as err:
##                        # should only happen to edge cases
##                        print "error getting",src_x,src_y,cellx,celly,col,row,err
##                        pass
##            #grid.img = newimg
##            #grid.cells = newimg.load()
##            #grid.img.show()
##            #newimg.save("C:/Users/BIGKIMO/Desktop/abc.png")
##            #fdsf

        # ONLY WIDTH HEIGHT APPROACH
##        newimg = PIL.Image.new("RGB",(self.data.width,self.data.height))
##        for grid in self.data:
##            print grid
##            gridget = grid.get
##            gridset = grid.set
##            for col,(x,tx) in enumerate(zip(xs,txs)):
##                #print "---",col
##                if tx == inf: continue
##                for row,(y,ty) in enumerate(zip(ys,tys)):
##                    if ty == inf: continue
##                    #print tx,ty
##                    src_x,src_y = destination2source(tx, ty)
##                    #print x,y
##                    #print tx,ty
##                    #print src_x,src_y
##                    #if not (xmin < src_x < xmax): continue
##                    #if not (ymin < src_y < ymax): continue
##                    #print src_x,src_y
##                    cellx,celly = geo_to_cell(src_x, src_y)
##                    #print cellx,celly
##                    #print col,row,cellx,celly
##                    try:
##                        #print x,y
##                        #print tx,ty
##                        #print src_x,src_y
##                        src_value = gridget(cellx,celly).value
##                        if src_value != 0:
##                            print (src_x,src_y,col,row,src_value)
##                        gridset(col, row, src_value)
##                        newimg.putpixel((col,row), src_value)
##                        #print "set", gridget(col,row)
##                        # random note: fromcell --> togeo --> totransfgeo --?-- totransfcell?
##                    except:
##                        # should only happen to edge cases
##                        print "error getting",src_x,src_y,cellx,celly
##            grid.img = newimg
##            grid.cells = newimg.load()
##            grid.img.show()
##            newimg.save("C:/Users/BIGKIMO/Desktop/abc.png")
##            #fdsf
                    
        
##        def dst_quad_to_src(quad):
##            src_quad = []
##            for dst_px in [(quad[0], quad[1]), (quad[0], quad[3]),
##                           (quad[2], quad[3]), (quad[2], quad[1])]:
##                dst_w = to_dst_w(dst_px)
##                print dst_w
##                src_w = pyproj.transform(wgs84, fromspace, dst_w)
##                src_px = to_src_px(src_w)
##                src_quad.extend(src_px)
##            return quad, src_quad
##
##        halfwidth,halfheight = self.data.info["cellwidth"]/2.0, self.data.info["cellheight"]/2.0
##        meshes = []
##        for cell in self.data.grids[0]:
##            print cell.x,cell.y
##            #x,y = cell.x,cell.y
##            #halfwidth,halfheight = 1,1
##            x,y = self.data.cell_to_geo(cell.x, cell.y)
##            corners = [x-halfwidth, y-halfheight,
##                       x-halfwidth, y+halfheight,
##                       x+halfwidth, y+halfheight,
##                       x+halfwidth, y-halfheight]
##            xs,ys = corners[::2], corners[1::2]
##            txs,tys = pyproj.transform(wgs84, fromspace, xs, ys)
##            tcorners = [xory for xy in zip(txs,tys) for xory in xy]
##            #tcorners = dst_quad_to_src(corners)
##            meshes.append((tcorners,corners))
##        print len(meshes)
##        dataimg = self.data.grids[0].img.transform((self.data.width,self.data.height),
##                                                   PIL.Image.MESH, meshes, PIL.Image.NEAREST)
##        
##        self.data.grids[0].img = dataimg
##        self.data.grids[0].pixels = dataimg.load()
##        print self.data.bbox

    def render(self, width, height, coordspace_bbox):
        
        info = self.data.info.copy()

        # position in space
        print (width,height,coordspace_bbox)
        print self.data.bbox
        positioned,mask = self.data.positioned(width, height, coordspace_bbox)
        print positioned.grids[0].img

        # first mask away value edges beyond raster extent
        # ...

        # additionally mask away nodata
##        nodata = info.get("nodata_value")
##        if nodata != None:
##            mask = PIL.Image.new("1", (positioned.width, positioned.height), 255)
##            px = mask.load()
##            for x in xrange(positioned.width):
##                for y in xrange(positioned.height):
##                    value = (band.cells[x,y] for band in positioned.grids)
##                    if all((val == nodata for val in value)):
##                        px[x,y] = 0
            #mask = PIL.Image.eval(img, lambda px: 0 if px == nodata else 255)
            #mask = mask.convert("1")
            #mask.save("mask.png")
            #img.putalpha(mask)
            #print img.mode
            #new = PIL.Image.new("RGBA", size, (0,0,0,0))
            #new.paste(img, (0,0), mask)
            #img = new

        # combine all data grids into one image for visualizing
        if len(positioned.grids) == 1:
            # greyscale if one band
            band1 = positioned.grids[0]
            img = band1.img.convert("RGB")
        else:
            # rgb of first three bands
            bands = [grid.img for grid in positioned.grids[:3] ]
            img = PIL.Image.merge("RGB", bands)

        # make edge and nodata mask transparent
        img.putalpha(mask)

##        # SET RASTER COORDSYS BASED ON INFO COEFFS
##        #xleft_coord, ytop_coord, xright_coord, ybottom_coord = self.data.bbox
##
##        # (old)
##        # define this coordinate space with pyagg
##        # ...so that we can get the reverse coordinate to pixel
##        #canvas = pyagg.canvas.from_image(img)
##        #canvas.custom_space(xleft_coord,ytop_coord,xright_coord,ybottom_coord)
##            
##        # GET COORDS OF ALL 4 VIEW SCREEN CORNERS
##        xleft,ytop,xright,ybottom = coordspace_bbox
##        viewcorners = [(xleft,ytop), (xleft,ybottom), (xright,ybottom), (xright,ytop)]
##        
##        # FIND PIXEL LOCS OF ALL THESE COORDS ON THE RASTER
##        viewcorners_pixels = [self.data.geo_to_cell(*point, fraction=True) for point in viewcorners]
##
##        # ON RASTER, PERFORM QUAD TRANSFORM
##        #(FROM VIEW SCREEN COORD CORNERS IN PIXELS TO RASTER COORD CORNERS IN PIXELS)
##        flattened = [xory for point in viewcorners_pixels for xory in point]
##        img = img.transform((width, height), PIL.Image.QUAD,
##                            flattened, resample=PIL.Image.NEAREST)

        # finally make nodata value transparent
##        nodata = 0 #info.get("nodata_value")
##        if nodata != None:
##            mask = img.copy()
##            bands = []
##            for band in mask.split():
##                px = band.load()
##                for x in xrange(mask.size[0]):
##                    for y in xrange(mask.size[1]):
##                        if px[x,y] == nodata:
##                            px[x,y] = 0
##                        else:
##                            px[x,y] = 255
##                bands.append(band)
##            mask = PIL.Image.merge(mask.mode, bands)
##            #mask = PIL.Image.eval(img, lambda px: 0 if px == nodata else 255)
##            mask = mask.convert("1")
##            #mask.save("mask.png")
##            img.putalpha(mask)
##            print img.mode
##            #new = PIL.Image.new("RGBA", size, (0,0,0,0))
##            #new.paste(img, (0,0), mask)
##            #img = new

        # final, coloring
        # determine coloring from .styleoptions
        # #1 gradient, from color gradient mapped to one band
        # #2 rgb, set r,g,b by using multiple bands in expression, eg red="band1/band2"
        img.save("test.png")
        self.img = img


