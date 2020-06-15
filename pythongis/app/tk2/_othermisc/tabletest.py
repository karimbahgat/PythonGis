import Tkinter as tk

fields = "one two three four five six".split()
table = [[row for col in xrange(6)] for row in xrange(770)]

class Cell(tk.Entry):
    def __init__(self, master, **kwargs):
        tk.Entry.__init__(self, master, **kwargs)

class Table(tk.Frame):
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        self.colwidth = 10
        self.rowheight = 20
        self.data = [[col for col in range(self.colwidth)] for row in range(self.rowheight)]
        self.new_position(0, 0)

    def set_data(self, data):
        pass

    def new_position(self, rowindex, columnindex):
        # first delete old cells
        # ...

        # then place new cells
        for rowi in range(rowindex, self.rowheight):
            for coli in range(columnindex, self.colwidth):
                value = self.data[rowi][coli]
                Cell(self, text=unicode(value)).grid(row=rowi, column=coli)

if __name__ == "__main__":
    win = tk.Tk()
    table = Table(win)
    table.pack(fill="both", expand=True)

    win.mainloop()



    


                
