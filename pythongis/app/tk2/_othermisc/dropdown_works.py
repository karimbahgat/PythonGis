
import Tkinter as tk

class Combobox(tk.Label):
    def __init__(self, master, choices=[], default=None, direction="down", arrowimage="default", **kwargs):
        style = {"relief": "groove", "bg":"white"}
        style.update(kwargs)
        tk.Label.__init__(self, master, **style)
        # options
        if direction not in ("down","up"):
            raise Exception("Direction must be either down or up")
        self.direction = direction
        self.choices = choices
        # entry
        self.entry = tk.Entry(self, bg=style["bg"], borderwidth=0)
        self.entry.pack(side="left", fill="y")
        if default != None:
            self.entry.insert(0, default)
        # dropdown arrow
        if arrowimage == "default":
            arrowimage = tk.PhotoImage(file="dropdown.gif")
        else: pass # image should be passed as a Photoimage
        self.arrow = tk.Label(self, bg=style["bg"], image=arrowimage)
        self.arrow.img = arrowimage
        self.arrow.pack(side="right")
        self.arrow.bind("<Button-1>", self.dropdown)

    def dropdown(self, event=None):
        self.arrow["relief"] = "sunken"
        self.entry.focus_force()
        self.entry.select_range(0, tk.END)
        menu = tk.Menu(self.entry, tearoff=0, bg="white")
        def changeentry(choice):
            self.entry.delete(0, tk.END)
            self.entry.insert(0, choice)
            self.rollup()
        if self.direction == "down": choices = self.choices
        elif self.direction == "up": choices = list(reversed(self.choices))
        for choice in choices:
            menu.add_command(label=repr(choice).ljust(30), command=lambda x=choice: changeentry(x))
        x = self.entry.winfo_rootx()
        if self.direction == "down":
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
        elif self.direction == "up":
            y = self.entry.winfo_rooty() - menu.yposition(0) #menu.winfo_height()
        menu.post(x, y)

    def rollup(self, event=None):
        self.arrow["relief"] = "flat"
        


if __name__ == "__main__":
    win = tk.Tk()

    OPTIONS = range(20)

    cbox = Combobox(win, choices=OPTIONS, default=12, direction="down")
    cbox.pack(side="left")
    cbox2 = Combobox(win, choices=OPTIONS, default=24, direction="up")
    cbox2.pack(side="left")


    win.mainloop()
