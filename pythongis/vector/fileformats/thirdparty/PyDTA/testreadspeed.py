

import sys
sys.path.append("C:/Users/kimo/Documents/GitHub")
import PyDTA

import stata_dta as st


##dta = st.open_dta("bleh/BDIR51FL.DTA")
##print dta

##import tably as tb
##dta = tb.Table("bleh/BDIR51FL.DTA")
##print dta

##dta = PyDTA.Reader(open("bleh/BDIR51FL.DTA","rb"))
##print dta, len(dta)
##
##import time
##t = time.time()
##for obs in dta.dataset():
##    pass
##print t-time.time()
##print "done"

#########

keepvars = ["caseid","v001","v105","v190"]

def datagen():
    import os
    for name in os.listdir("Junk/bleh"):
        if name.lower().endswith(".dta"):
            dta = PyDTA.Reader(open("Junk/bleh/%s"%name,"rb"))
            yield dta

##for dta in datagen():
##    import tk2
##    win = tk2.Tk()
##    fr = tk2.ScrollFrame(win)
##    fr.pack()
##    for var in dta.variables():
##        #_row = tk2.Label(fr)
##        nm = tk2.Label(fr, text=var.name)
##        nm.pack()#side="left")
##        #lb = tk2.Label(_row, text=var.label)
##        #lb.pack(side="right")
##        #_row.pack()
##    win.mainloop()

out = st.Dta115([])
for dta in datagen():
    # add any new vars
    for var in dta.variables():
        if var.name in keepvars and var.name not in out._varlist:
            typcode = (range(251)+list('bhlfd')).index(var.type)
            print var.name, var.value_format, var.type, typcode
            out.append_var(var.name, [], typcode)
            if var.label:
                out.label_variable(var.name, var.label)
            if var.value_format:
                mapping = dta.value_labels()[var.value_format]
                #mapping = dict(((k,bytes(v)) for k,v in mapping.items()))
                print mapping
                out.label_define(var.name, mapping, modify=True)
                out.label_values(var.name, var.value_format)

for dta in datagen():
    # append observations
    print dta
    for obs in dta.dataset(as_dict=True):
        row = [obs[name] if name in obs else None for name in out._varlist]
        out.append_obs(row)
    print len(out)

out.save("out.dta")
        

