#!/usr/bin/python

from StataTools import Reader
from StataTypes import MissingValue

if __name__ == '__main__':
    import sys
    dta_file = Reader(file(sys.argv[1]))
    for v in dta_file.variables():
        attr = filter(lambda x: x[0] != '_', dir(v))
        print v, dict(zip(attr, map(lambda x: getattr(v, x), attr)))
    c = 0; m = 0
    for x in dta_file.dataset():
        c += 1
        print x
        if len(filter(lambda x: x is None, x)):
            m += 1
    print '%d of %d observations (%d missing) from %s.' % (c, len(dta_file), m, sys.argv[1])
