
import Tkinter as tk
import time

class TableView(tk.Frame):
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        self.cellwidth = 40
        self.cellheight = 20
        self.screencorner = (0,0)
        self.table = None
        def update_view(event):
            self.update_view()
        self.after(100, self.update_view)
        #self.resized = time.time()
        #self.bind("<Configure>", update_view)

        # place scrollbars
##        def verticalscrollbarpressed(event):
##            sliderclicked = event.widget.identify(event.x, event.y)
##            print sliderclicked
##            if sliderclicked == "slider":
##                event.widget.dragging = True
##        def verticalscrollbarreleased(event):
##            if event.widget.dragging == True:
##                print event.widget.get()
##                rel_slidertop = event.widget.get()[1]
##                rel_viewtop = rel_slidertop / float(self.totalheight)
##                rel_viewbottom = (rel_slidertop + self.viewheight) / float(self.totalheight)
##                print rel_viewtop, rel_viewbottom
##                event.widget.set(rel_viewtop, rel_viewbottom)
##                event.widget.dragging = False


                
        def vertical_yview(eventtype, rel_slidertop):
            if eventtype == "moveto":
                # move tableview
                curcol,currow = self.screencorner
                topcell = self.totalheight * float(rel_slidertop)
                bottomcell = topcell + self.viewheight
                midcell = sum([topcell,bottomcell]) / 2.0
                print midcell
                #self.scroll_to_cell(column=curcol, row=int(round(midcell)))
                # reanchor scrollbar
                rel_sliderbottom = bottomcell / float(self.totalheight)
                self.verticalscrollbar.set(rel_slidertop, rel_sliderbottom)
            
        self.verticalscrollbar = tk.Scrollbar(self,
                                              repeatinterval=2000,
                                              repeatdelay=2000)
        self.verticalscrollbar.config(command=vertical_yview)
        self.verticalscrollbar.pack(side="right", fill="y")
        #self.verticalscrollbar.bind("<Button-1>", verticalscrollbarpressed)
        #self.verticalscrollbar.bind("<ButtonRelease-1>", verticalscrollbarreleased)
        self.tablearea = tk.Frame(self)
        self.tablearea.pack(side="left", fill="both", expand=True)
        
        #self.horizontalscrollbar = tk.Scrollbar(self.tablearea, orient=tk.HORIZONTAL)
        #self.horizontalscrollbar.pack(side="bottom", fill="x")
        #...

    def set_data(self, data):
        self.fields = data.pop(0)
        self.data = data

    @property
    def totalwidth(self):
        return len(self.data[0])

    @property
    def totalheight(self):
        return len(self.data)

    @property
    def viewwidth(self):
        screenpixelwidth = self.winfo_width()
        cells_in_screenwidth = screenpixelwidth / float(self.cellwidth)
        actual_cells = min(cells_in_screenwidth, self.totalwidth)
        return int(round(actual_cells))

    @property
    def viewheight(self):
        screenpixelheight = self.winfo_height()
        cells_in_screenheight = screenpixelheight / float(self.cellheight)
        cells_in_screenheight -= 1 # to make room for one row of fields
        actual_cells = min(cells_in_screenheight, self.totalheight)
        return int(round(actual_cells))

    def scroll_by_cells(self, columns, rows):
        curcol,currow = self.screencorner
        self.screencorner = int(curcol + columns), int(currow + rows)
        self.update_view()

    def scroll_by_percent(self, colperc, rowperc):
        columns = self.totalwidth * colperc
        rows = self.totalheight * rowperc
        self.scroll_by_cells(columns, rows)
        
    def scroll_to_cell(self, column, row):
        self.screencorner = int(column), int(row)
        self.update_view()

    def scroll_to_percent(self, colperc, rowperc):
        column = self.totalwidth * colperc
        row = self.totalheight * rowperc
        self.scroll_to_cell(column, row)

    def update_view(self):
        oldtable = self.table
    
        # make new table
        print "upperleft cell:", self.screencorner
        print "windowsize, pixels:", self.winfo_width(), self.winfo_height()
        print "windowsize, cells:", self.viewwidth, self.viewheight
        curcol,currow = self.screencorner
        self.table = tk.Frame(self.tablearea)
        rowslice = slice(currow, currow + self.viewheight)
        colslice = slice(curcol, curcol + self.viewwidth)
        for f,field in enumerate(self.fields[colslice]):
            cellframe = tk.Frame(self.table, width=self.cellwidth, height=self.cellheight)
            cellframe.grid(column=f, row=0)
            cellframe.grid_propagate(False)
            cell = tk.Label(cellframe, bg="black", fg="white")
            cell.place(relwidth=1, relheight=1)
            cell["text"] = field
        for r,row in enumerate(self.data[rowslice]):
            r += 1
            for c,value in enumerate(row[colslice]):
                cellframe = tk.Frame(self.table, width=self.cellwidth, height=self.cellheight)
                cellframe.grid(column=c, row=r)
                cellframe.grid_propagate(False)
                cell = tk.Entry(cellframe)
                cell.place(relwidth=1, relheight=1)
                cell.insert(0, value)
        self.table.place(relwidth=1, relheight=1)
                
        # finally, destroy old table
        if oldtable:
            oldtable.destroy()


if __name__ == "__main__":
    
    w,h = 40,100000
    data = [["f%i"%i for i in range(w)]]
    data += [["%i,%i"%(col,row) for col in range(w)] for row in range(h)]

    window = tk.Tk()
    tableview = TableView(window, width=400, height=200)
    tableview.pack(fill="both", expand=True)
    tableview.set_data(data)
    print "table total dims", tableview.totalwidth, tableview.totalheight
    
    tk.Button(window, text="Refresh", command=tableview.update_view).pack()
    def testmove():
        tableview["width"] += 20
        tableview["height"] += 20
        tableview.scroll_by_percent(0.10, 0.10)
    tk.Button(window, text="Test move", command=testmove).pack()

    window.mainloop()
