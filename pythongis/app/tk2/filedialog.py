
import sys
if sys.version.startswith("2"):
    from tkFileDialog import askopenfile, askopenfilename, asksaveasfile, asksaveasfilename, askdirectory
else:
    from tkinter.filedialog import askopenfile, askopenfilename, asksaveasfile, asksaveasfilename, askdirectory
