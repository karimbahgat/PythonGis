
import itertools, operator
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely


# TODO: when multiple input, uses all possible combinations, but need a way to use spatial indexes etc


# SQL components

def aggreg(iterable, aggregfuncs, geomfunc=None):
    """Each func must be able to take an iterable and return a single item.
    Aggregfuncs is a series of 3-tuples: an output column name, a value function or value hash index on which to base the aggregation, and a valid string or custom function for aggregating the retieved values.
    """
    def lookup_geomfunc(agg):
        # handle aliases
        if agg == "dissolve":
            agg = "union"
        elif agg == "unique":
            agg = "difference"

        # detect
        if agg == "intersection":
            def _func(fs):
                gs = (f.get_shapely() for f in fs if f.geometry)
                cur = next(gs)
                for g in gs:
                    if not g.is_empty:
                        cur = cur.intersection(g)
                return cur.__geo_interface__
            
        elif agg == "difference":
            def _func(fs):
                gs = (f.get_shapely() for f in fs if f.geometry)
                cur = next(gs)
                for g in gs:
                    if not g.is_empty:
                        cur = cur.difference(g)
                return cur.__geo_interface__

        elif agg == "union":
            def _func(fs):
                gs = [f.get_shapely() for f in fs if f.geometry]
                if len(gs) > 1:
                    from shapely.ops import cascaded_union
                    return cascaded_union(gs).__geo_interface__
                elif len(gs) == 1:
                    return gs[0].__geo_interface__

        elif hasattr(agg, "__call__"):
            # agg is not a string but a custom function
            return agg

        else:
            raise Exception("geomfunc must be a callable function or a valid set geometry string name")

        return _func
    
    def lookup_aggfunc(agg):
        # handle aliases
        if agg in ("average","avg"):
            agg = "mean"

        # detect
        if agg == "count": return len
        elif agg == "sum": return sum
        elif agg == "max": return max
        elif agg == "min": return min
        elif agg == "first": return lambda seq: seq.__getitem__(0)
        elif agg == "last": return lambda seq: seq.__getitem__(-1)
        elif agg == "majority": return lambda seq: max(itertools.groupby(sorted(seq)), key=lambda(gid,group): len(list(group)))[0]
        elif agg == "minority": return lambda seq: min(itertools.groupby(sorted(seq)), key=lambda(gid,group): len(list(group)))[0]
        elif agg == "mean": return lambda seq: sum(seq)/float(len(seq))
        elif isinstance(agg, basestring) and agg.endswith("concat"):
            delim = agg[:-6]
            return lambda seq: delim.join((str(v) for v in seq))
        elif hasattr(agg, "__call__"):
            # agg is not a string but a function
            return agg
        else:
            raise Exception("aggfunc must be a callable function or a valid statistics string name")

    def check_valfunc(valfunc):
        if hasattr(valfunc,"__call__"):
            pass
        elif isinstance(valfunc,(str,unicode)):
            hashindex = valfunc
            valfunc = lambda f: f[hashindex]
        else:
            raise Exception("valfunc for field '%s' must be a callable function or a string of the hash index for retrieving the value"%name)
        return valfunc
    
    aggregfuncs = [(name,check_valfunc(valfunc),aggname,lookup_aggfunc(aggname)) for name,valfunc,aggname in aggregfuncs]

    def make_number(value):
        try: return float(value)
        except: return None

    def is_missing(val):
        return val is None or (isinstance(val, float) and math.isnan(val))

    iterable = list(iterable)
    row = []
    for _,valfunc,aggname,aggfunc in aggregfuncs:
        values = (valfunc(item) for item in iterable)

        # missing values are not considered when calculating stats
        values = [val for val in values if not is_missing(val)] 
        
        if aggname in ("sum","max","min","mean"):
            # only consider number values if numeric stats
            values = [make_number(value) for value in values if make_number(value) != None]

        if values:
            aggval = aggfunc(values)
        else:
            aggval = "" # or best with None
            
        row.append(aggval)

    if geomfunc:
        geomfunc = lookup_geomfunc(geomfunc)
        geom = geomfunc(iterable)
        return row,geom

    else:
        return row

def select(iterable, columnfuncs, geomfunc=None):
    if geomfunc:
        # iterate and yield rows and geoms
        for item in iterable:
            row = [func(item) for name,func in columnfuncs]
            geom = geomfunc(item)
            yield row,geom

    else:
        # iterate and yield rows
        for item in iterable:
            row = [func(item) for name,func in columnfuncs]
            yield row

def where(iterable, condition):
    for item in iterable:
        if condition(item):
            yield item

def groupby(iterable, key):
    
    if hasattr(key,"__call__"):
        pass
    elif isinstance(key,(str,unicode)):
        hashindex = key
        key = lambda f: f[hashindex]
    elif isinstance(key,(list,tuple)) and all((isinstance(v,(str,unicode)) for v in key)):
        hashindexes = key
        key = lambda f: tuple((f[h] for h in hashindexes))
    else:
        raise Exception("groupby key must be a callable function or a string or list/tuple of strings of the hash index(es) for retrieving the value(s)")

    iterable = sorted(iterable, key=key)
    for groupid,items in itertools.groupby(iterable, key=key):
        yield items

def limit(iterable, n):
    for i,item in enumerate(iterable):
        if i < n:
            yield item
        else:
            break

def query(_from, _select, _geomselect=None, _where=None, _groupby=None, _limit=None):
    """Takes a series of sql generator components, runs them, and iterates over the resulting feature-geom tuples.

    Arg _from must be a sequence of one or more iterables.
    All combinations of items from the iterables are then tupled together and passed to the remaining _select, _where_, and _groupby args.
    This allows us to involve items from all the iterables in the functions that define our queries.
    The final _select function should return a row list, and the _geomselect should return a geojson dictionary.
    """
    # INSTEAD MAKE INTO CLASS
    # WITH .fields attr
    # AND .__iter__()
    # AND .get_vectordata()
    # AND MAKE EACH YIELDED ROW A VECTOR FEATURE CLASS
    # THIS WAY ALLOWING CHAINED QUERIES

    # parse args
    iterables = _from
    columnfuncs = _select
    geomfunc = _geomselect
    condition = _where
    key = _groupby
    n = _limit
    
    # first yield header as list of column names
    colnames = [each[0] for each in columnfuncs]
    yield colnames

    # make an iterable that yields every combinaion of all input iterables' items
    if len(iterables) == 1:
        iterable = iterables[0]
    else:
        iterable = itertools.product(*iterables)

    # iterate and add
    if key:
        groups = groupby(iterable, key)

        # limit
        if n:
            groups = limit(groups, n)
        
        for items in groups:
            # filter
            if condition:
                items = where(items, condition)
                
            # aggregate
            # NOTE: columnfuncs and geomfunc must expect an iterable as input and return a single row,geom pair
            item = aggreg(items, columnfuncs, geomfunc)
            yield item
            
    else:
        # filter
        if condition:
            iterable = where(iterable, condition)

        # limit
        if n:
            iterable = limit(iterable, n)

        # select
        for item in select(iterable, columnfuncs, geomfunc):
            yield item

def query_to_data(_query):
    # create table and columns
    out = VectorData()
    header = next(_query)
    out.fields = [name for name in header]

    # add each feature
    for row,geom in _query:
        if geom: # hack, should find a way to add empty geoms
            out.add_feature(row, geom)

    return out



##########
# EXPERIMENTAL

class Iterable(object):
    def __init__(self, iterable):
        self.it = iterable

    def __iter__(self):
        for item in self.it:
            yield item

    def intersects(self, othercol):
        for item in self.quick_overlap(othercol.bbox):
            for otheritem in othercol.quick_overlap(self.bbox):
                if item.intersects(otheritem):
                    yield item





