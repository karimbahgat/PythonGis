
import sys
if sys.version.startswith("2"):
    from tkMessageBox import showinfo, showwarning, showerror, askquestion, askokcancel, askyesno, askretrycancel
else:
    from tkinter.messagebox import showinfo, showwarning, showerror, askquestion, askokcancel, askyesno, askretrycancel
