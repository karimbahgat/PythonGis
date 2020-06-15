from Tkinter import *
root = Tk()

panes = PanedWindow(root, sashrelief="raised")
panes.pack(fill="both", expand="yes")

left = Label(panes, text="Left Pane")
left.pack()

right = Label(panes, text="Right Pane")
right.pack()

panes.add(left)
panes.add(right)

root.mainloop()
