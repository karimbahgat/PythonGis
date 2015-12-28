
import itertools, operator
from .data import *

import shapely, shapely.ops, shapely.geometry
from shapely.prepared import prep as supershapely



# SQL components

def aggreg(iterable, aggregfuncs, geomfunc):
    """Each func must be able to take an iterable and return a single item.
    Aggregfuncs is a series of 3-tuples: an output column name, a value function on which to base the aggregation, and a valid string or custom function for aggregating the retieved values.
    """
    def lookup_aggfunc(agg):
        if agg == "count": return len
        elif agg == "sum": return sum
        elif agg == "max": return max
        elif agg == "min": return min
        elif agg == "first": return lambda seq: seq.__getitem__(0)
        elif agg == "last": return lambda seq: seq.__getitem__(-1)
        elif agg == "majority": notyet
        elif agg == "minority": notyet
        elif agg == "average": return lambda seq: sum(seq)/float(len(seq))
        else:
            # agg is not a string, and is assumed already a function
            return agg

    aggregfuncs = [(name,valfunc,aggname,lookup_aggfunc(aggname)) for name,valfunc,aggname in aggregfuncs]

    def make_number(value):
        try: return float(value)
        except: return None

    iterable = list(iterable)
    row = []
    for _,valfunc,aggname,aggfunc in aggregfuncs:
        values = [valfunc(item) for item in iterable]
        
        if aggname in ("sum","max","min","average"):
            # only consider number values if numeric stats
            values = [make_number(value) for value in values if make_number(value) != None]

        if values:
            aggval = aggfunc(values)
        else:
            aggval = "" # or best with None
            
        row.append(aggval)

    print "row",row
        
    geom = geomfunc(iterable)

    return row,geom

def select(iterable, columnfuncs, geomfunc):
    # iterate and yield rows and geoms
    for item in iterable:
        row = [func(item) for name,func in columnfuncs]
        geom = geomfunc(item)
        yield row,geom

def where(iterable, condition):
    for item in iterable:
        if condition(item):
            yield item

def groupby(iterable, key):
    iterable = sorted(iterable, key=key)
    for groupid,items in itertools.groupby(iterable, key=key):
        yield items

def limit(iterable, n):
    for i,item in enumerate(iterable):
        if i < n:
            yield item
        else:
            break

def query(_from, _select, _geomselect, _where=None, _groupby=None, _limit=None):
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
            row,geom = aggreg(items, columnfuncs, geomfunc)
            yield row,geom
            
    else:
        # filter
        if condition:
            iterable = where(iterable, condition)

        # limit
        if n:
            iterable = limit(iterable, n)

        # select
        for row,geom in select(iterable, columnfuncs, geomfunc):
            yield row,geom

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
