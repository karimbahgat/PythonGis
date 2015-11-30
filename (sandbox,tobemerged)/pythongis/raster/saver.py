
import PIL
import PIL.TiffImagePlugin
import PIL.TiffTags

def to_file(grids, info, filepath):
    if filepath.endswith((".ascii",".asc")):
        # create header
        width, height = img.size()
        xorig, yorig = info["xy_geo"]
        if info["cell_anchor"] == "center":
            xorigtype = "xllcenter"
            yorigtype = "yllcenter"
        elif info["cell_anchor"] == "sw":
            xorigtype = "xllcorner"
            yorigtype = "yllcorner"
        else:
            raise Exception("Currently not saving rasters with anchor points other than sw or center")
        header = ""
        header += "NCOLS %s \n"%width
        header += "NROWS %s \n"%height
        header += "%s %s \n"%(xorigtype,xorig)
        header += "CELLSIZE %s \n"%info["cellwidth"]
        header += "NODATA_VALUE %s \n"%None
        # write bands
        filename_root, ext = os.path.splitext(filepath)
        for i, grid in enumerate(grids):
            (img, cells) = grid
            newpath = filename_root + "_" + i + ext
            tempfile = open(newpath, "w")
            # write header
            tempfile.write(header)
            # write cells
            for y in xrange(height):
                row = " ".join((str(cells[x,y]) for x in xrange(width)))+"\n"
                tempfile.write(row)
            tempfile.close()

    else:
        # combine and prep final image
        if len(grids) == 1:
            img = grids[0].img
        elif len(grids) == 3:
            # merge all images together
            mode = "RGB"
            bands = [grid.img for grid in grids]
            img = PIL.Image.merge(mode, bands)
        elif len(grids) == 4:
            # merge all images together
            mode = "RGBA"
            bands = [grid.img for grid in grids]
            img = PIL.Image.merge(mode, bands)
        else:
            # raise error if more than 4 bands, bc PIL cannot save such images
            raise Exception("Cannot save more than 4 bands to one file; split and save each band separately")

        # save to file
        if filepath.endswith((".tif", ".tiff", ".geotiff")):           
            # write directly to tag info
            PIL.TiffImagePlugin.WRITE_LIBTIFF = False
            tags = PIL.TiffImagePlugin.ImageFileDirectory()
            if info.get("cell_anchor"):
                # GTRasterTypeGeoKey, aka midpoint pixels vs topleft area pixels
                if info.get("cell_anchor") == "center":
                    # is area
                    tags[1025] = 1.0
                    tags.tagtype[1025] = 12 #double, only works with PIL patch
                elif info.get("cell_anchor") == "nw":
                    # is point
                    tags[1025] = 2.0
                    tags.tagtype[1025] = 12 #double, only works with PIL patch
            if info.get("transform_coeffs"):
                # ModelTransformationTag, aka 4x4 transform coeffs...
                tags[34264] = tuple(map(float,info.get("transform_coeffs")))
                tags.tagtype[34264] = 12 #double, only works with PIL patch
            else:
                if info.get("xy_cell") and info.get("xy_geo"):
                    # ModelTiepointTag
                    x,y = info["xy_cell"]
                    geo_x,geo_y = info["xy_geo"]
                    tags[33922] = tuple(map(float,[x,y,0,geo_x,geo_y,0]))
                    tags.tagtype[33922] = 12 #double, only works with PIL patch
                if info.get("cellwidth") and info.get("cellheight"):
                    # ModelPixelScaleTag
                    scalex,scaley = info["cellwidth"],info["cellheight"]
                    tags[33550] = tuple(map(float,[scalex,scaley,0]))
                    tags.tagtype[33550] = 12 #double, only works with PIL patch
            if info.get("nodata_value"):
                tags[42113] = bytes(info.get("nodata_value"))
                tags.tagtype[42113] = 2 #ascii
                
            # finally save the file using tiffinfo headers
            img.save(filepath, tiffinfo=tags)

        elif filepath.endswith(".png"):
            # save
            img.save(filepath)
            # write .pgw world file
            # ...
            pass

        elif filepath.endswith(".jpg"):
            # save
            img.save(filepath)
            # write .jgw world file
            # ...
            pass
