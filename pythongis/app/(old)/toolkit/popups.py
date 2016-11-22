
# Import GUI helpers
import Tkinter as tk
import tkMessageBox

# Import internals
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

class RunToolFrame(tk.Frame): 
    def __init__(self, master=None, **kwargs):
        # Make this class a subclass of tk.Toplevel and add to it
        tk.Frame.__init__(self, master, **kwargs)
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
        # Make run button at bottom
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
        # ...because this window might be destroyed, so use its master
        dispatch.after_completion(self.master, pending, finish)



