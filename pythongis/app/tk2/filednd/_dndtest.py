
import tk2

root = tk2.Tk()
root.center()

frame = tk2.Frame(root)
frame.pack()

entry = tk2.Text(frame)
entry.pack()

def handle(event):
    print type(event.data), event.data
    for f in event.data:
        event.widget.insert("insert", f+"\n")
    
entry.bind_dnddrop(handle, "Files") #"Text")

root.mainloop()
