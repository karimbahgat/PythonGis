
# Import builtins
import inspect

# Import GUI helpers
import Tkinter as tk
import tkMessageBox
from .buttons import IconButton, OkButton, CancelButton
from . import dispatch
from ... import vector


# Define some styles
from . import theme
style_options_helptext = {"font": theme.font1["type"],
                          "fg": theme.font1["color"]}
style_options_titles = {"font": theme.titlefont1["type"],
                        "fg": theme.titlefont1["color"]}
style_options_labels = {"font": theme.font1["type"],
                      "fg": theme.font1["color"]}



# Popup Windows

def popup_message(parentwidget, errmsg):
    tkMessageBox.showwarning("Warning", errmsg)

class Window(tk.Toplevel):
    def __init__(self, master=None, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        tk.Toplevel.__init__(self, master, **kwargs)
        # Set its size to percent of screen size, and place in middle
        width = self.winfo_screenwidth() * 0.6
        height = self.winfo_screenheight() * 0.6
        xleft = self.winfo_screenwidth()/2.0 - width / 2.0
        ytop = self.winfo_screenheight()/2.0 - height / 2.0
        self.geometry("%ix%i+%i+%i"%(width, height, xleft, ytop))
        # Force and lock focus to the window
        self.grab_set()
        self.focus_force()

class RunToolWindow(Window): 
    def __init__(self, master=None, **kwargs):
        # Make this class a subclass of tk.Toplevel and add to it
        Window.__init__(self, master, **kwargs)
        # Create empty option and input data
        self.hidden_options = dict()
        self.inputs = list()
        self.statusbar = None
        self.method = None
        self.process_results = None
        # Make helpscreen area to the right
        self.helpscreen = tk.Frame(self)
        self.helpscreen.pack(side="right", fill="y")
        self.helptitle = tk.Label(self.helpscreen, text="Help Screen", **style_options_titles)
        self.helptitle.pack(fill="x")
        self.helptext = tk.Text(self.helpscreen, width=30,
                                wrap=tk.WORD, cursor="arrow",
                                **style_options_helptext)
        self.helptext.pack(fill="both", expand=True)
        # Make main screen where input goes to the left
        self.mainscreen = tk.Frame(self)
        self.mainscreen.pack(side="left", fill="both", expand=True)
        self.maintitle = tk.Label(self.mainscreen, text="User Input", **style_options_titles)
        self.maintitle.pack()
        self.mainoptions = tk.Frame(self.mainscreen)
        self.mainoptions.pack(fill="both", expand=True)
        self.mainbottom = tk.Frame(self.mainscreen)
        self.mainbottom.pack()
        # Make cancel and run button at bottom
        self.cancelbut = CancelButton(self.mainbottom, command=self.destroy)
        self.cancelbut.pack(side="left")
        self.runbut = OkButton(self.mainbottom, command=self.run)
        self.runbut.pack(side="right")

    def assign_statusbar(self, statusbar):
        self.statusbar = statusbar
        
    def set_target_method(self, taskname, method):
        self.taskname = taskname
        self.method = method
        # use the method docstring as the help text
        doc = method.__doc__
        if doc:
            # clean away tabs, multispaces, and other junk
            cleandoc = method.__doc__.strip().replace("\t","").replace("  "," ")
            # only keep where there are two newlines after each other
            # bc single newlines are likely just in-code formatting
            cleandoc = "\n\n".join(paragraph.replace("\n","").strip() for paragraph in cleandoc.split("\n\n") )
            helptext = cleandoc
        else:
            helptext = "Sorry, no documentation available..."
        self.helptext.insert(tk.END, helptext)
        self.helptext["state"] = tk.DISABLED
        
##        # automatically build input widgets from method arguments
##        args, varargs, keywords, defaults = inspect.getargspec(method)
##        for i, arg in enumerate(args):
##            if arg == "self": continue
##            tk.Label(self, text=arg).grid(row=i, column=0)
##            tk.Entry(self).grid(row=i, column=1)

    def set_finished_method(self, method):
        self.process_results = method

    def add_option_input(self, label, valuetype, argname=None, multi=False, length=None, default=None, minval=None, maxval=None, choices=None):
        optionrow = tk.Frame(self.mainoptions)
        optionrow.pack(fill="x", anchor="n", pady=5, padx=5)
        if multi:
            # make a list-type widget that user can add to
            inputlabel = tk.Label(optionrow, text=label, **style_options_labels)
            inputlabel.pack(side="left", anchor="nw", padx=3)
            inputwidget = tk.Listbox(optionrow, activestyle="none",
                                     highlightthickness=0, selectmode="extended",
                                     **style_options_labels)
            inputwidget.pack(side="right", anchor="ne", padx=3)
            
            if choices:
                # add a listbox of choices to choose from
                def addtolist():
                    for selectindex in fromlist.curselection():
                        selectvalue = fromlist.get(selectindex)
                        inputwidget.insert(tk.END, selectvalue)
                    for selectindex in reversed(fromlist.curselection()):
                        fromlist.delete(selectindex)
                def dropfromlist():
                    for selectindex in inputwidget.curselection():
                        selectvalue = inputwidget.get(selectindex)
                        fromlist.insert(tk.END, selectvalue)
                    for selectindex in reversed(inputwidget.curselection()):
                        inputwidget.delete(selectindex)
                # define buttons to send back and forth bw choices and input
                buttonarea = tk.Frame(optionrow)
                buttonarea.pack(side="right", anchor="n")
                addbutton = IconButton(buttonarea, command=addtolist,
                                       text="-->", **style_options_labels)
                addbutton.pack(anchor="ne", padx=3, pady=3)
                dropbutton = IconButton(buttonarea, command=dropfromlist,
                                       text="<--", **style_options_labels)
                dropbutton.pack(anchor="ne", padx=3, pady=3)
                # create and populate the choices listbox
                fromlist = tk.Listbox(optionrow, activestyle="none",
                                     highlightthickness=0, selectmode="extended",
                                     **style_options_labels)
                for ch in choices:
                    fromlist.insert(tk.END, ch)
                fromlist.pack(side="right", anchor="ne", padx=3)
            else:
                # add a freeform entry field and button to add to the listbox
                def addtolist():
                    entryvalue = addentry.get()
                    inputwidget.insert(tk.END, entryvalue)
                    addentry.delete(0, tk.END)
                def dropfromlist():
                    for selectindex in reversed(inputwidget.curselection()):
                        inputwidget.delete(selectindex)
                buttonarea = tk.Frame(optionrow)
                buttonarea.pack(side="right", anchor="n")
                addbutton = IconButton(buttonarea, command=addtolist,
                                       text="-->", **style_options_labels)
                addbutton.pack(anchor="ne", padx=3, pady=3)
                dropbutton = IconButton(buttonarea, command=dropfromlist,
                                       text="<--", **style_options_labels)
                dropbutton.pack(anchor="ne", padx=3, pady=3)
                # place the freeform text entry widget
                addentry = tk.Entry(optionrow, **style_options_labels)
                addentry.pack(side="right", anchor="ne", padx=3)

        else:
            inputlabel = tk.Label(optionrow, text=label, **style_options_labels)
            inputlabel.pack(side="left", anchor="nw")
            if choices:
                # dropdown menu of choices
                choice = tk.StringVar()
                if default: choice.set(default)
                inputwidget = tk.OptionMenu(optionrow, choice, *choices)
                inputwidget.choice = choice
                inputwidget.pack(side="right", anchor="ne", padx=3)
            else:
                # simple number or string entry widget
                inputwidget = tk.Entry(optionrow, **style_options_labels)
                inputwidget.pack(side="right", anchor="ne")
                if default != None:
                    inputwidget.insert(tk.END, str(default))

        # remember for later
        inputwidget.meta = dict(argname=argname, label=label, choices=choices,
                                valuetype=valuetype, multi=multi, length=length,
                                default=default, minval=minval, maxval=maxval)            
        self.inputs.append(inputwidget)

    def add_hidden_option(self, argname, value):
        self.hidden_options[argname] = value

    def get_options(self):
        args = list()
        kwargs = dict()
        for key,val in self.hidden_options.items():
            if key == None: args.extend(val) #list arg
            else: kwargs[key] = val
        for inputwidget in self.inputs:
            argname = inputwidget.meta["argname"]
            multi = inputwidget.meta["multi"]
            choices = inputwidget.meta["choices"]
            valuetype = inputwidget.meta["valuetype"]
            
            # ensure within min/max range
            def validate(value):
                minval = inputwidget.meta["minval"]
                if minval and not value >= minval:
                    return Exception("The input value for %s was smaller than the minimum value %s" %(inputwidget.meta["label"], minval))
                maxval = inputwidget.meta["maxval"]
                if maxval and not value <= maxval:
                    return Exception("The input value for %s was larger than the maximum value %s" %(inputwidget.meta["label"], minval))
                return value
                
            # get value based on the argument type
            if argname == None:
                # if argname is None, then it is not a kwarg, but unnamed arg list
                get = inputwidget.get(0, last=tk.END)
                if get != "":
                    args.extend( [validate(valuetype(val)) for val in get] )
            elif multi:
                get = inputwidget.get(0, last=tk.END)
                if get != "":
                    kwargs[argname] = [ validate(valuetype(val)) for val in get ]
            elif choices:
                get = inputwidget.choice.get()
                if get != "":
                    kwargs[argname] = validate(valuetype(get))
            else:
                get = inputwidget.get()
                if get != "":
                    kwargs[argname] = validate(valuetype(get))
        return args,kwargs

    def run(self):
        # first ensure the tool has been prepped correctly
        if not self.statusbar:
            raise Exception("Internal error: The tool has not been assigned a statusbar")
        if not self.method:
            raise Exception("Internal error: The tool has not been assigned a method to be run")
        if not self.process_results:
            raise Exception("Internal error: The tool has not been assigned how to process the results")
        
        # get options
        try:
            args,kwargs = self.get_options()
        except Exception as err:
            popup_message(self, "Invalid options: \n" + str(err) )
            return

        # start statusbar
        self.statusbar.task.start(self.taskname)

        # run task
        pending = dispatch.request_results(self.method, args=args, kwargs=kwargs)
        print "running tool", self.method, args, kwargs

        # schedule to process results upon completion
        def finish(results):
            # first run user specified processing
            try:
                self.process_results(results)
            except Exception as err:
                popup_message(self, "Error processing results:" + "\n\n" + str(err) )
            # then stop the task
            self.statusbar.task.stop()
        # note: this window cannot be the one to schedule the listening
        # ...because this window will be destroyed, so use its master
        dispatch.after_completion(self.master, pending, finish)

        # close the options window
        self.destroy()


##class RunToolWindow_SingleData(RunToolWindow):
##    def __init__(self, master, **kwargs):
##        """
##        Note, this type of tool window takes only one datasource, so
##        it requires that its master/parent is a LayerItem.
##        """
##        # Make this class a subclass and add to it
##        RunToolWindow.__init__(self, master, **kwargs)
##
##        # Auto set some options from its master layeritem
##        self.layeritem = master
##        self.layerspane = self.layeritem.layerspane
##        self.assign_statusbar(self.layerspane.statusbar)
##        self.add_hidden_option(argname="data", value=self.layeritem.renderlayer.data)
##
##class RunToolWindow_MultiData(RunToolWindow):
##    def __init__(self, master, **kwargs):
##        """
##        Note, this type of tool window requires that its master/parent
##        is a Toolbar inside a Tab inside a Ribbon.
##        """
##        # Make this class a subclass and add to it
##        RunToolWindow.__init__(self, master, **kwargs)
##        
##        # Auto set some options from its master layeritem
##        #self.toolbar = master.master
##        #self.tab = self.toolbar.master
##        #self.ribbon = self.tab.master.master
##        #self.assign_statusbar(self.ribbon.statusbar)







#################

## USEFUL POPUP TOOLTIP INFO WHEN HOVERING
## FROM http://www.voidspace.org.uk/python/weblog/arch_d7_2006_07_01.shtml#e387
##class ToolTip(object):
##
##    def __init__(self, widget):
##        self.widget = widget
##        self.tipwindow = None
##        self.id = None
##        self.x = self.y = 0
##
##    def showtip(self, text):
##        "Display text in tooltip window"
##        self.text = text
##        if self.tipwindow or not self.text:
##            return
##        x, y, cx, cy = self.widget.bbox("insert")
##        x = x + self.widget.winfo_rootx() + 27
##        y = y + cy + self.widget.winfo_rooty() +27
##        self.tipwindow = tw = Toplevel(self.widget)
##        tw.wm_overrideredirect(1)
##        tw.wm_geometry("+%d+%d" % (x, y))
##        try:
##            # For Mac OS
##            tw.tk.call("::tk::unsupported::MacWindowStyle",
##                       "style", tw._w,
##                       "help", "noActivates")
##        except TclError:
##            pass
##        label = Label(tw, text=self.text, justify=LEFT,
##                      background="#ffffe0", relief=SOLID, borderwidth=1,
##                      font=("tahoma", "8", "normal"))
##        label.pack(ipadx=1)
##
##    def hidetip(self):
##        tw = self.tipwindow
##        self.tipwindow = None
##        if tw:
##            tw.destroy()
##
##def createToolTip(widget, text):
##    toolTip = ToolTip(widget)
##    def enter(event):
##        toolTip.showtip(text)
##    def leave(event):
##        toolTip.hidetip()
##    widget.bind('<Enter>', enter)
##    widget.bind('<Leave>', leave)
