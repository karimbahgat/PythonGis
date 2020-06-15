'''The SuperText class inherits from Tkinter's Text class and provides added
functionality to a standard text widget:

- Option to turn scrollbar on/off
- Right-click pop-up menu
- Two themes included (terminal and typewriter)

Compliant with Python 2.5-2.7

Author: @ifthisthenbreak
http://code.activestate.com/recipes/578897-supertext-scrollable-text-with-pop-up-menu-and-the/

Expanded on by Karim Bahgat, 2015
'''


# Imports

import sys
if sys.version.startswith("2"):
    import Tkinter as tk
    from Tkinter import Frame, Text, Scrollbar, Menu
    from tkMessageBox import askokcancel
else:
    import tkinter as tk
    from tkinter import Frame, Text, Scrollbar, Menu
    from tkMessageBox import askokcancel

import ttk
from . import mixins as mx
from . import basics as bs
from . import messagebox as msg
from . import colorchooser as clr
from . import scrollwidgets as scr


# Classes

class MultiTextSearch(scr.Frame):
    def __init__(self, master, stylename, highlightstyle, imgs={}, **kwargs):
        scr.Frame.__init__(self, master, **kwargs)
        
        self.namevar = tk.StringVar(self)
        self.namevar.set(stylename)
        self.style = highlightstyle.copy()
        self.searchterms = []
        self.dependents = []
        self.imgs = imgs
        
        # add visuals
        self.header = bs.Label(self, textvariable=self.namevar)
        self.header.pack() #grid(row=0, column=0, columnspan=2, sticky="w")

        def _changecolor():
            rgb,hexdec = clr.askcolor()
            self.style["background"] = rgb
            self.colorselect.set_color(rgb)
            self.highlight()
        self.colorselect = bs.ColorButton(self, command=_changecolor)
        self.colorselect.set_color(self.style["background"], width=15, height=15)
        self.colorselect.pack()

        self.entry = bs.Entry(self)
        self.entry.pack() #grid(row=1, column=0, sticky="w")

        def _add_term(*pointless):
            term = self.entry.get()
            self.add_searchterm(term)
            self.entry.delete("0", "end")
            
        self.addbut = bs.Button(self, text="+", command=_add_term)
        self.addbut.pack() #grid(row=1, column=1, sticky="w")
        if "addbut" in self.imgs:
            self.addbut.set_icon(**self.imgs["addbut"])

        self.entry.bind("<Return>", _add_term, "+")

        self.termlist = scr.ScrollFrame(self)
        self.termlist.pack(fill="both", expand=1) #grid(row=2, column=0, sticky="w")

    def add_searchterm(self, searchterm):
        if searchterm.strip():
            # create term variable
            termvar = tk.StringVar(self)
            termvar.set(searchterm)

            # add visual term representation
            termlabel = SearchTerm(self.termlist, textvariable=termvar, imgs=self.imgs)
            termlabel.pack(fill="x")

            # link and remember termvar and widget
            termlabel.var = termvar
            termlabel.multitext = self
            termvar.widget = termlabel
            self.searchterms.append(termvar)
            self.highlight()

    def highlight(self, easysearch=True, **kwargs):

        # for all connected textwidgets
        for textwidget in self.dependents:

            # configure highlightstyle
            stylename = self.namevar.get()
            textwidget.clear_highlights(stylename)
            preppedstyle = self.style.copy()
            preppedstyle["background"] = "#%02x%02x%02x" % preppedstyle["background"]
            textwidget.tag_configure(stylename, **preppedstyle)
            
            # search all terms
            for termvar in self.searchterms:
                term = termvar.get()

                # highlight text
                if easysearch:
                    # easy stata-like search syntax
                    term = easy_searchpattern_to_regex(term)
                    count = textwidget.highlight_pattern(term,
                                                        stylename,
                                                        nocase=True,
                                                        exact=False,
                                                        regexp=True)
                else:
                    # raw syntax of either exact match or complex regex, depending on kwargs
                    count = textwidget.highlight_pattern(term,
                                                        stylename,
                                                        **kwargs)
                    
                if count:
                    # mark the terms in the termlist if at least one was found
                    termvar.widget["background"] = "#%02x%02x%02x" % self.style["background"]
                else:
                    # reset to normal
                    termvar.widget["background"] = "light grey" # NOT SURE IS CORRECT COLOR, SWITCH TO COLOR TEMPLATES...


def easy_searchpattern_to_regex(term):
    term = term.replace("*", "\\w*") # wildcards must be part of the same word
    term = term.replace(".", "\\.") # allow matching periods literally

    # term (including wildcards) only applies to one word at a time
    # if term starts or ends with alphanumeric char, force bound the term to the closest wordbreak
    # otherwise, it is already ending with wordbreak, so adding an additional wordbreak regex will
    # ...actually result in no match (eg in acronyms like u.s.a.)
    if term[-1].isalnum():
        term = term + "\\y"
    if term[0].isalnum():
        term = "\\y" + term

    # in this version acronyms will match (but spaces at start or end will fail)
    #term = "".join(["(?:\W+|^)",   # instead of wordbreak, preceding char is a nonword char or start of text
    #                "(%s)" % term,   # look for the term
    #                "(?:\W+|$)"])   # instead of wordbreak, proceding char is a nonword char or end of text

    return term


class SearchTerm(bs.Label):
    def __init__(self, master, imgs={}, **kwargs):
        bs.Label.__init__(self, master)

        self.label = bs.Label(self, **kwargs)
        self.label.pack(side="left", fill="x", expand=1)

        self.imgs = imgs

        # delete button
        self.delbut = bs.Button(self, text="X", command=self._destroy)
        self.delbut.pack(side="right")
        if "delbut" in self.imgs:
            self.delbut.set_icon(**self.imgs["delbut"])

        # next/prev buttons
        def seeterm(forward=True):
            for textwidget in self.multitext.dependents:
                term = self.var.get()
                    
                if forward:
                    result = textwidget.next_pattern(term,
                                                     current="insert",
                                                    nocase=True,
                                                    exact=False,
                                                    regexp=True)
                else:
                    result = textwidget.prev_pattern(term,
                                                     current="insert",
                                                    nocase=True,
                                                    exact=False,
                                                    regexp=True)
                    
                if result:
                    startpos,endpos = result
                    textwidget.see(endpos)
                    textwidget.mark_set("insert", endpos)
        
        self.nextbut = bs.Button(self, text=">", command=lambda: seeterm(forward=True))
        self.nextbut.pack(side="right")
        if "nextbut" in self.imgs:
            self.nextbut.set_icon(**self.imgs["nextbut"])
        self.prevbut = bs.Button(self, text="<", command=lambda: seeterm(forward=False))
        self.prevbut.pack(side="right")
        if "prevbut" in self.imgs:
            self.prevbut.set_icon(**self.imgs["prevbut"])

    def _destroy(self):
        proceed = msg.askokcancel("Delete term?", "You are about to delete a term from the list of relevance terms. Are you sure you want to continue?")
        if proceed:
            self.multitext.searchterms.remove(self.var)
            self.multitext.highlight()
            self.destroy()

    def __setitem__(self, key, value):
        # configure properties for both the main and the subwidgets
        self.label[key] = value
        self.__dict__[key] = value
        

class Text(mx.AllMixins, tk.Text):
    
    def __init__(self, parent, scrollbar=True, **kw):

        parent = mx.get_master(parent)
        self.parent = parent
        
        frame = Frame(parent)
        frame.pack(fill='both', expand=True)
        
        # text widget
        if "wrap" not in kw:
            kw["wrap"] = "word"
        tk.Text.__init__(self, frame, **kw)
        #self.pack(side='left', fill='both', expand=True)
        mx.AllMixins.__init__(self, parent)
        
        # scrollbar
        if scrollbar:
            scrb = Scrollbar(frame, orient='vertical', command=self.yview) 
            self.config(yscrollcommand=scrb.set)
            scrb.pack(side='right', fill='y')
        
        # pop-up menu
        self.popup = Menu(self, tearoff=0)
        self.popup.add_command(label='Cut', command=self._cut)
        self.popup.add_command(label='Copy', command=self._copy)
        self.popup.add_command(label='Paste', command=self._paste)
        self.popup.add_separator()
        self.popup.add_command(label='Select All', command=self._select_all)
        self.popup.add_command(label='Clear All', command=self._clear_all)
        self.bind('<Button-3>', self._show_popup)

        # only allow mouse scroll when mouse inside text
        self.bind("<Leave>", lambda event: self.winfo_toplevel().focus_set(), "+")
        self.bind("<Enter>", lambda event: self.focus_set(), "+")
        
    def apply_theme(self, theme='standard'):
        '''theme=['standard', 'typewriter', 'terminal']'''

        if theme == 'typewriter':
            '''takes all inserted text and inserts it one char every 100ms'''
            options = {"font": ('Times', 10, 'bold')}
            self.config(options)
            text = self.get('1.0', 'end')
            self.delete('1.0', 'end')
            self.char_index = 0
            self._typewriter([char for char in text])
            
        elif theme == 'terminal':
            '''blocky insert cursor'''
            options = {'bg': 'black', 'fg': 'white', 'font': ('Courier', 10)}
            self.config(options)
            self.cursor = '1.0'
            self.fg = self.cget('fg')
            self.bg = self.cget('bg')
            self.switch = self.fg
            self.config(insertwidth=0)
            self._blink_cursor()
            self._place_cursor()

        elif theme == 'matrix':
            '''blocky insert cursor'''
            options = {'bg': 'black', 'fg': 'green', 'font': ('Courier', 10)}
            self.config(options)
            self.cursor = '1.0'
            self.fg = self.cget('fg')
            self.bg = self.cget('bg')
            self.switch = self.fg
            self.config(insertwidth=0)
            self._blink_cursor()
            self._place_cursor()

    def highlight_pattern(self, pattern, tag, start="1.0", end="end",
                          regexp=False, nocase=True, exact=True, **kwargs):
        '''Apply the given tag to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression.

        From: http://stackoverflow.com/questions/3781670/how-to-highlight-text-in-a-tkinter-text-widget
        '''

        if not pattern:
            return 0
        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.search(pattern, "matchEnd", "searchLimit",
                                count=count, regexp=regexp, nocase=nocase,
                                exact=exact, **kwargs)
            if index: 
                self.mark_set("matchStart", index)
                self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
                self.tag_add(tag, "matchStart", "matchEnd")
            else:
                break
        return count.get()

    def clear_highlights(self, *tagnames):
        names = tagnames or self.tag_names()
        self.tag_delete(*names)

    def next_pattern(self, pattern, current,
                     regexp=False, nocase=True, exact=True, **kwargs):
        if not pattern:
            return None
        start = self.index(current)
        end = self.index("end")

        count = tk.IntVar()
        index = self.search(pattern, start, end,
                            count=count, regexp=regexp, nocase=nocase,
                            exact=exact, **kwargs)
        if index:
            return index, index+"+%sc"%count.get()
        else:
            return None

    def prev_pattern(self, pattern, current,
                     regexp=False, nocase=True, exact=True, **kwargs):
        if not pattern:
            return None
        start = self.index(current)
        end = self.index("1.0")

        count = tk.IntVar()
        index = self.search(pattern, start, end,
                            count=count, regexp=regexp, nocase=nocase,
                            exact=exact, backwards=True, **kwargs)
        if index:
            return index, index+"-%sc"%count.get()
        else:
            return None


    # MISC INTERNALS

    def _show_popup(self, event):
        '''right-click popup menu'''
        
        if self.parent.focus_get() != self:
            self.focus_set()
        
        try:
            self.popup.post(event.x_root, event.y_root)
        finally:
            self.popup.grab_release()
            
    def _cut(self):
        
        try:
            selection = self.get(*self.tag_ranges('sel'))
            self.clipboard_clear()
            self.clipboard_append(selection)
            self.delete(*self.tag_ranges('sel'))
        except TypeError:
            pass
    
    def _copy(self):
        
        try:
            selection = self.get(*self.tag_ranges('sel'))
            self.clipboard_clear()
            self.clipboard_append(selection)
        except TypeError:
            pass
        
    def _paste(self):
        
        self.insert('insert', self.selection_get(selection='CLIPBOARD'))
        
    def _select_all(self):
        '''selects all text'''
        
        self.tag_add('sel', '1.0', 'end-1c')
        
    def _clear_all(self):
        '''erases all text'''
        
        isok = askokcancel('Clear All', 'Erase all text?', parent=self,
                           default='ok')
        if isok:
            self.delete('1.0', 'end')

    def _typewriter(self, text): # theme: typewriter
        '''after the theme is applied, this method takes all the inserted text
        and types it out one character every 100ms'''

        self.insert('insert', text[self.char_index])
        self.char_index += 1

        if hasattr(self, "typer") and self.char_index == len(text):
            self.after_cancel(self.typer)
        else:
            self.typer = self.after(100, self._typewriter, text)

    def _place_cursor(self): # theme: terminal
        '''check the position of the cursor against the last known position
        every 15ms and update the cursorblock tag as needed'''

        current_index = self.index('insert')

        if self.cursor != current_index:
            self.cursor = current_index
            self.tag_delete('cursorblock')
            
            start = self.index('insert')
            end = self.index('insert+1c')
            
            if start[0] != end[0]:
                self.insert(start, ' ')
                end = self.index('insert')
                
            self.tag_add('cursorblock', start, end)
            self.mark_set('insert', self.cursor)

        self.after(15, self._place_cursor)

    def _blink_cursor(self): # theme: terminal
        '''alternate the background color of the cursorblock tagged text
        every 600 milliseconds'''
        
        if self.switch == self.fg:
            self.switch = self.bg
        else:
            self.switch = self.fg

        self.tag_config('cursorblock', background=self.switch)

        self.after(600, self._blink_cursor)


