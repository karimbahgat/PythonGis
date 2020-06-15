######################################################################
# Seritt Extensions:
# Date: 02262005
# Class ComboBox
# Add this section to your Tkinter.py file in 'PYTHONPATH/Lib/lib-tk/'
# Options: width, border, background, foreground, fg, bg, font
#	, relief, cursor, exportselection, selectbackgroun,
#selectforeground, height
#
# Methods: activate(int index) => int, curselection() => int,
#delete(item=["ALL" or int], start=int, end=["END" or
# int],
# focus_set()/focus(), get()=>selected string in box, pack(padx=int,
#pady=int, fill(X, Y, BOTH), expand=bool, # side=LEFT,
# RIGHT, TOP, BOTTOM, CENTER
#
# http://www.thecodingforums.com/threads/searching-for-a-combobox-for-tkinter.342592/

import Tkinter as tk

class ComboBox:
    ITEMS = range(0)

    def __init__(self, parent, width=None, border=1, background=None,
                 foreground=None, fg=None, bg=None, font=None,
                 relief=None, cursor=None, exportselection=None, values=[],
                 selectbackground=None, selectforeground=None, height=None):
        self.frame = tk.Frame(parent)
        self.entry = tk.Entry(self.frame, width=None, border=border,
            background=background, foreground=foreground, fg=fg, bg=bg, font=font,
            relief=relief, cursor=cursor, exportselection=exportselection,
            selectbackground=selectbackground, selectforeground=selectforeground,
            height=height)
        self.entry.pack(fill="x")
        self.scroll = tk.Scrollbar(self.frame)
        self.scroll.pack(side="right", fill="y")
        self.listbox = tk.Listbox(self.frame, 
            yscrollcommand=self.scroll.set, width=None, border=border,
            background=background, foreground=foreground, fg=fg, bg=bg, font=font,
            relief=relief, cursor=cursor, exportselection=exportselection,
            selectbackground=selectbackground, selectforeground=selectforeground,
            height=height)
        self.listbox.pack(fill="x")
        self.scroll.config(command=self.listbox.yview)
        for i, value in enumerate(values):
            self.insert(i, value)
        self.listbox.bind("<ButtonPress-1>", self.change_entry)

    def activate(self, index):
        self.listbox.activate(index)

    def curselection(self):
        return map(int, self.listbox.curselection())[0]

    def delete(self, item=None, start=None, end=None):
        if item=='ALL':
            self.listbox.delete(0, END)
        elif start == None and end == None:
            self.listbox.delete(item)
        else:
            self.listbox.delete(start, end)

    def get_focus(self):
        self.entry.get_focus()

    def focus(self):
        self.entry.get_focus()

    def get(self):
        return self.entry.get()

    def pack(self, padx=None, pady=None, fill=None, expand=None, side=None):
        self.frame.pack(padx=padx,
                        pady=pady,
                        fill=fill,
                        expand=expand,
                        side=side)

    def size(self):
        return self.listbox.size()

    def insert(self, START, ITEM):
        self.ITEMS.append(ITEM)
        self.listbox.insert(START, ITEM)
        self.listbox.select_set(0)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.listbox.get(self.listbox.curselection()))

    def change_entry(self, event):
        def i(event):
            try:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, self.listbox.get(self.listbox.curselection()))
            except:
                pass
        self.listbox.bind("<ButtonRelease-1>", i)


if __name__ == "__main__":
    window = tk.Tk()
    combo = ComboBox(window, values=range(10))
    combo.pack()
    window.mainloop()



