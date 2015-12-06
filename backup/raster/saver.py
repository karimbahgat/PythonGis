
# import PIL as the saver
import PIL
import PIL.TiffImagePlugin
import PIL.TiffTags

def to_file(bands, info, filepath):
    def combine_bands(bands):
        # saving in image-like format, so combine and prep final image
        if len(bands) == 1:
            img = bands[0].img
            return img
        elif len(bands) == 3:
            # merge all images together
            mode = "RGB"
            bands = [band.img for band in bands]
            img = PIL.Image.merge(mode, bands)
            return img
        elif len(bands) == 4:
            # merge all images together
            mode = "RGBA"
            bands = [band.img for band in bands]
            img = PIL.Image.merge(mode, bands)
            return img
        else:
            # raise error if more than 4 bands, because PIL cannot save such images
            raise Exception("Cannot save more than 4 bands to one file; split and save each band separately")
    def create_world_file(savepath, geotrans):
        dir, filename_and_ext = os.path.split(savepath)
        filename, extension = os.path.splitext(filename_and_ext)
        world_file_path = os.path.join(dir, filename) + ".wld"
        with open(world_file_path, "w") as writer:
            # rearrange transform coefficients and write
            xscale,xskew,xoff,yskew,yscale,yoff = geotrans
            writer.writelines([xscale,yskew,xskew,yscale,xoff,yoff])

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
        header += "NODATA_VALUE %s \n"%info["nodata_value"]
        # write bands
        filename_root, ext = os.path.splitext(filepath)
        for i, band in enumerate(bands):
            (img, cells) = band
            newpath = filename_root + "_" + i + ext
            with open(newpath, "w") as tempfile:
                # write header
                tempfile.write(header)
                # write cells
                for y in xrange(height):
                    row = " ".join((str(cells[x,y]) for x in xrange(width)))+"\n"
                    tempfile.write(row)
            # finally create world file for the geotransform
            create_world_file(newpath, info["transform_coeffs"])

    elif filepath.endswith((".tif", ".tiff", ".geotiff")):
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
        img = combine_bands(bands)
        img.save(filepath, tiffinfo=tags)

    elif filepath.endswith((".jpg",".jpeg",".png",".bmp",".gif")):
        # save
        img = combine_bands(bands)
        img.save(filepath)
        # write world file
        create_world_file(filepath, info["transform_coeffs"])


