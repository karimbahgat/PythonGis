

import sys
sys.path.append("C:/Users/kimo/Documents/GitHub")
import PyDTA




dta = PyDTA.Reader(open("Junk/bleh/BDIR51FL.DTA","rb"))
print dta
for var in dta.variables():
    print var.name, var.label
    if var.value_format:
        print var.value_format
        print dta.value_labels()[var.value_format]

