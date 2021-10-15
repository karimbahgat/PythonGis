import pythongis as pg

# setup map
mymap = pg.renderer.Map(500, 250, "blue")
mymap.add_layer(r"C:\Users\kimo\Downloads\ne_10m_admin_1_states_provinces\ne_10m_admin_1_states_provinces.shp",
                dataoptions=dict(encoding="latin"),
                #fillcolor={"breaks":"natural","key":lambda f:f["name_len"],"valuestops":[(255,0,0),(0,255,0)]},
                legendoptions=dict(title="Length of province name", valueformat=".1f"),
                )

layout = pg.renderer.Layout(500,250)
layout.add_map(mymap)
layout.add_map(mymap)
layout.add_map(mymap)#,xy=(50,50))
layout.add_legend(xy=("1%w","99%h"), anchor="sw",
                 legendoptions=dict(padding=0, fillcolor=None, outlinecolor=None, anchor="center"),
                 )

# view single
layout.view()





### --------------------
##
### play with variations
##mymap.todo("Time","lyrname","year","split","equal",classes=5) # create five new map classes with only a subset of the specified layer filtered in each
##mymap.todo("Region","zoom_bbox",[1,1,22,22],[1,1,22,22],[1,1,22,22]) # new map classes zoomed at different points
##
### final?
##mymap.tiled("Time") # one map with all time categories gridded on one map
##mymap.tiled("Region","Time") # one map with all region-time value combinations gridded on one map, region varying slowest
##mymap.tiled("Time", groupby="Region") # ...
##
### or maybe just
##mymap.groupby("Region") # groupby instead of tiled, all region zoom varieties gridded on one map
##mymap.groupby("Region","Time") # all region-time combis gridded
##
### or best as:
##fig = figure(mymap) # just a single map
##fig = figure(mymap, groupby=["Region"]) # this is how to create a gridded region map
##fig = figure(mymap, groupby=["Time"]) # and here is a gridded time map
##fig = figure(mymap, Region="CentralAfrica", groupby="Time") # can also fix a dimension at some value
##
### allowing multiple grid maps as:
##for reg in mymap.dimensions["Region"]:
##    fig = figure(mymap, Region=reg, groupby="Time")
##
### what about more dimensions, would that get messy with loops, so maybe instead do:
### each figure would be a unique region-violencetype group, using the last dimension Time as the gridded variation
### and each maps would be a batch object of all maps containing the batch dimvalues,
### the whole batch figure titled with the group dims, and each map in the grid titled with its specific last dimvalue
### when adding dimension an option to specify how to make the dimvalues more readable in title maybe or too much?
##for maps in mymap.batches("Region","Violtype","Time"):
##    fig = figure(*maps)
##
### so maybe even allow specifying one batch for specific colums or rows for comparison?
### ...
##
### conclusion
##mymap.batch("Time") or figure(mymap, groupby="Time") # creates a single gridded figure with automatic title, submap labels, and shared legend
##mymap.batches("Region","Violtype","Time") or figures(mymap,groupby=["Region","Violtype","Time"]) # creates multiple figures for each combination on fimensions, each with auto rendering
##
##
##
##
##
#################
##
### A
##mymap.groupby("Region")
##mymap.tiled("Time") # makes whole map, one for each time value
##mymap.view()
##
### B
##for regmap in mymap.groupby("Region"):
##    regmap.tiled("Time") # makes whole map, one for each time value
##    regmap.view()
##
### C
##mymap.tiled("Time", groupby="Region") # not sure how
##
### ------------------------
##













### view batch combinations
##mymap.add_dimension("Region", [("nw",lambda m:m.zoom_bbox(-180,90,0,0) ),
##                                ("se",lambda m:m.zoom_bbox(0,0,180,-90) ),
##                                 ])
##
##for dimdict,submap in mymap.iter_dimensions():
##    submap.render_all()
##    submap.view()
    
