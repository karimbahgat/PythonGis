"""
Contains the main functionality for end-users. 
"""

from __future__ import division
from . import breaks as _breaks
import itertools
import math



class Classifier(object):
    """
    A convenience class for managing a set of items/values according to a classification.
    Upon initiation the classifier uses the input values to calculate the breakpoints and class values.
    The classifier can then be iterated through to yield a tuple of the original items along
    with the symbolic class value representing the group they belong to.

    Attributes:

    - items: The list of items or values managed by the classifier.
    - algo: The name of the algorithm used to calculate the breakpoints, or 'custom' if the
        breakpoints were manually specified. 
    - breaks: Calculated list of break points. 
    - classvalues: The original bounds/gradient of symbolic values to assign to each of the classes. 
    - classvalues_interp: The interpolated gradient of symbolic values, one for each class grouping. 
    - key: Function used to extract value from each item, defaults to None and treats item itself as the value.
    - kwargs: The kwargs to pass to the algorithm function.
            The algorithm functions and their arguments can be found in `classypie.breaks`.
    """
    
    def __init__(self, items, breaks, classvalues, key=None, **kwargs):
        """
        Args:

        - **items**: The list of items or values to classify.
        - **breaks**: List of custom break values, or the name of the algorithm to use.
            Valid names are:
            - histogram (alias for equal)
            - equal
            - quantile
            - pretty
            - stdev
            - natural
            - headtail
            - log (base-10, uses offset to handle 0s but not negative numbers)
            - proportional
        - classvalues: A gradient of symbolic values to assign to each of the classes. The lowest class is assigned
            the first classvalue, the highest class is assigned the last classvalue, and classes in between are
            interpolated between the classvalue bounds and/or any midpoints if given. 
            Each entry can be either a single number or sequences of numbers
            where a classvalue will be interpolated for each sequence number,
            and so all sequences must be equally long. Thus, specifying the
            classvalues as rgb color tuples will create interpolated color gradients.
        - **key** (optional): Function used to extract value from each item, defaults to None and treats item itself as the value.
        - **extrabreaks** (optional): Force insert additional break points. These are added to the original breakpoints,
            so if the classification resulted in 5 groupings, and you insert 2 additional break values, the final classification
            will contain 7 groupings. 
        - **classes** (optional): The number of classes to group the items into. Needed for some break types but not others. 
        - **exclude** (optional): A list of values defining which values to exclude.
        - **minval** (optional): Sets the lower value boundary for the classification groupings, ignoring values below this threshold.
        - **maxval** (optional): Sets the upper value boundary for the classification groupings, ignoring values above this threshold.
        - **kwargs** (optional): Depending on the breaks algorithm used, any remaining kwargs are passed to the algorithm function.
            The algorithm functions and their arguments can be found in `classypie.breaks`.
        """
        
        self.items = items
        
        if isinstance(breaks, bytes):
            algo = breaks
            breaks = None
            
        else:
            algo = "custom"
            breaks = breaks
            
        self.algo = algo
        self.breaks = breaks
        self.classvalues = classvalues # the raw preinterpolated valuestops of the classvalues
        self.key = key
        self.kwargs = kwargs
        self.classvalues_interp = None # the final interpolated classvalues

        self.update()

    def __repr__(self):
        import pprint
        metadict = dict(algo=self.algo,
                        breaks=self.breaks,
                        classvalues_interp=self.classvalues_interp)
        return "Classifier object:\n" + pprint.pformat(metadict, indent=4)

    def update(self):
        """
        Force update/calculate breaks and class values based on the item values.
        Automatically called when initiating the classifier, but can be useful for
        recalculating if the classifier attributes have been modified. 
        Mostly used internally. 
        """
        # force update/calculate breaks and class values
        # mostly used internally, though can be used to recalculate
        if self.algo == "unique":
            self.classvalues_interp = self.classvalues

        elif self.algo == "proportional":
            self.classvalues_interp = [self.classvalues[0], self.classvalues[-1]]
            items,values = zip(*rescale(self.items,
                                       newmin=self.classvalues_interp[0],
                                       newmax=self.classvalues_interp[-1],
                                       key=self.key,
                                       **self.kwargs))
            itemvals = [self.key(item) for item in items]
            if self.classvalues_interp[0] < self.classvalues_interp[-1]:
                minval,maxval = min(itemvals), max(itemvals)
            else:
                minval,maxval = max(itemvals), min(itemvals)
            self.breaks = [minval,maxval]

        else:
            if self.algo != "custom":
                self.breaks = breaks(items=self.items,
                                    algorithm=self.algo,
                                    key=self.key,
                                    **self.kwargs)
            self.classvalues_interp = class_values(len(self.breaks)-1, # -1 because break values include edgevalues so will be one more in length
                                                   self.classvalues)

    def __iter__(self):
        # loop and yield items along with their classnum and classvalue
        
        if self.algo == "unique":
            if isinstance(self.classvalues_interp, dict):
                # only return specified uniqueval-classval pairs
                for uid,subitems in unique(self.items, key=self.key, **self.kwargs):
                    if uid in self.classvalues_interp:
                        classval = self.classvalues_interp[uid]
                        for item in subitems:
                            yield item,classval
            else:
                # eternally iterate over classvalues for each unique value
                def classvalgen ():
                    while True:
                        for classval in self.classvalues_interp:
                            yield classval
                classvalgen = classvalgen()
                for uid,subitems in unique(self.items, key=self.key, **self.kwargs):
                    classval = next(classvalgen)
                    for item in subitems:
                        yield item,classval

        elif self.algo == "proportional":
            for item,newval in rescale(self.items,
                                       newmin=self.classvalues_interp[0],
                                       newmax=self.classvalues_interp[-1],
                                       key=self.key,
                                       **self.kwargs):
                yield item,newval

        else:
            for valrange,subitems in split(self.items, self.breaks, key=self.key, **self.kwargs):
                midval = (valrange[0] + valrange[1]) / 2.0
                classinfo = self.find_class(midval)
                if classinfo is not None:
                    classnum,_ = classinfo
                    classval = self.classvalues_interp[classnum-1] # index is zero-based while find_class returns 1-based
                    for item in subitems:
                        yield item,classval

    def find_class(self, value):
        """
        Given this classifier's breakpoints, calculate which two breakpoints an input
        value is located between, returning the class number (1 as the first class)
        and the two enclosing breakpoint values. A value that is not between any of
        the breakpoints, ie larger or smaller than the break endpoints, is considered
        to be a miss and returns None.
        Mostly used internally. 

        Args:

        - **value**: The value for which to find the class. 

        Returns:

        - Return a tuple of the class number (1 as the first class) and the two
            enclosing breakpoint values. If value is outside the scope of all breakpoints,
            returns None.
        """
        return find_class(value, self.breaks)


################################
            

def find_class(value, breaks):
    """
    Given a set of breakpoints, calculate which two breakpoints an input
    value is located between, returning the class number (1 as the first class)
    and the two enclosing breakpoint values. A value that is not between any of
    the breakpoints, ie larger or smaller than the break endpoints, is considered
    to be a miss and returns None.

    Args:

    - **value**: The value for which to find the class. 
    - **breaks**: A list of break points that define the class groupings.

    Returns:

    - Return a tuple of the class number (1 as the first class) and the two
        enclosing breakpoint values. If value is outside the scope of all breakpoints,
        returns None. 
    """
    
    prevbrk = breaks[0]
    classnum = 1
    for nextbrk in breaks[1:]:
        if eval(bytes(prevbrk)) <= eval(bytes(value)) <= eval(bytes(nextbrk)):
            return classnum, (prevbrk,nextbrk)
        prevbrk = nextbrk
        classnum += 1
    else:
        # Value was not within the range of the break points
        return None

def class_values(classes, valuestops):
    """
    Given a range of valuestops (minimum, [...], maximum) of length n, linearly interpolate between those values
    to a new list of length m. Useful for creating representative numeric or rgb color values for each grouping in
    a classification.

    Example:

        >>> minmax = [0, 100]
        >>> interp = classypie.class_values(5, minmax)
        [0.0, 25.0, 50.0, 75.0, 100.0]

        >>> colorgradient = [(0,255,0), (255,255,0), (255,0,0)] # green, yellow, red
        >>> interp = classypie.class_values(5, colorgradient)
        >>> for col in interp:
        >>>     col
        [0.0, 255.0, 0.0]   # green
        [127.5, 255.0, 0.0] # green-yellow
        [255.0, 255.0, 0.0] # yellow
        [255.0, 127.5, 0.0] # orange
        [255.0, 0.0, 0.0]   # red

    Args:

    - classes: Number of class values to interpolate to. 
    - valuestops: The gradient of values representing the bounds (and optional midpoints) to interpolate
        between. Each entry can be either a single number or sequences of numbers
        where a classvalue will be interpolated for each sequence number,
        and so all sequences must be equally long. Thus, specifying the
        valuestops as rgb color tuples will create interpolated color gradients.

    Returns:

    - A list of values the length of the number of classes, linearly interpolated between the input valuestops. 
    """
    # special case
    if classes <= 1:
        #raise Exception("Number of classes must be higher than 1")
        return [valuestops[0]]
    if len(valuestops) < 2:
        raise Exception("There must be at least two items in valuestops for interpolating between")

    def _lerp(val, oldfrom, oldto, newfrom, newto):
        oldrange = oldto - oldfrom
        relval = (val - oldfrom) / float(oldrange)
        newrange = newto - newfrom
        newval = newfrom + newrange * relval
        return newval

    # determine appropriate interp func for either sequenes or single values
    
    if all(hasattr(valstop, "__iter__") for valstop in valuestops):
        _len = len(valuestops[0])
        if any(len(valstop) != _len for valstop in valuestops):
            raise Exception("If valuestops are sequences they must all have the same length")
        def _interpfunc(val):
            relindex = _lerp(classnum, 0, classes-1, 0, len(valuestops)-1)
            fromval = valuestops[int(math.floor(relindex))]
            toval = valuestops[int(math.ceil(relindex))]
            classval = [_lerp(relindex, int(relindex), int(relindex+1), ifromval, itoval)
                        for ifromval,itoval in zip(fromval,toval)]
            return classval
    else:
        def _interpfunc(classnum):
            relindex = _lerp(classnum, 0, classes-1, 0, len(valuestops)-1)
            fromval = valuestops[int(math.floor(relindex))]
            toval = valuestops[int(math.ceil(relindex))]
            classval = _lerp(relindex, int(relindex), int(relindex+1), fromval, toval)
            return classval
    
    # perform
    classvalues = []
    for classnum in range(classes):
        classval = _interpfunc(classnum)
        classvalues.append(classval)

    return classvalues

def breaks(items, algorithm, key=None, extrabreaks=None, exclude=None, minval=None, maxval=None, **kwargs):
    """
    Given a list of items or values, classify into groups and get their break points, including the start and endpoint.

    Args:

    - **items**: The list of items or values to classify.
    - **algorithm**: Name of the classification algorithm to use.
        Valid names are:
        - histogram (alias for equal)
        - equal
        - quantile
        - pretty
        - stdev
        - natural
        - headtail
        - log (base-10, uses offset to handle 0s but not negative numbers)
    - **key** (optional): Function used to extract value from each item, defaults to None and treats item itself as the value.
    - **extrabreaks** (optional): Force insert additional break points. These are added to the original breakpoints,
        so if the classification resulted in 5 groupings, and you insert 2 additional break values, the final classification
        will contain 7 groupings. 
    - **classes** (optional): The number of classes to group the items into. Needed for some break types but not others. 
    - **exclude** (optional): A list of values defining which values to exclude.
    - **minval** (optional): Sets the lower value boundary for the classification groupings, ignoring values below this threshold.
    - **maxval** (optional): Sets the upper value boundary for the classification groupings, ignoring values above this threshold.
    - **kwargs** (optional): Depending on the breaks algorithm used, any remaining kwargs are passed to the algorithm function.
        The algorithm functions and their arguments can be found in `classypie.breaks`.

    Returns:

    - List of break points calculated for this algorithm in increasing order, i.e. the dividing lines between groupings. 
    """

    # ensure values are numeric
    def forcenumber(val):
        try:
            val = float(val)
            return val
        except:
            return None
    
    # sort by key
    if key:
        keywrap = lambda x: forcenumber(key(x))
    else:
        keywrap = forcenumber
        
    items = (item for item in items if keywrap(item) is not None)
    if exclude is not None:
        if not isinstance(exclude, (list,tuple)): exclude = [exclude]
        items = (item for item in items if keywrap(item) not in exclude)
    if minval is not None: items = (item for item in items if keywrap(item) >= minval)
    if maxval is not None: items = (item for item in items if keywrap(item) <= maxval)
    items = sorted(items, key=keywrap)
    values = [keywrap(item) for item in items]

    # get breaks
    func = _breaks.__dict__[algorithm]
    breaks = func(values, **kwargs)

    # insert extra breaks (list of single break values or pairs)
    if extrabreaks:
        for val in extrabreaks:
            oldbreaks = list(breaks)
            
            # insert single break value anywhere after first same or greater breakpoint
            # (remember that duplicate breakpoints will collect only that specific value)
            prevbrk = oldbreaks[0]
            i = 0
            for nextbrk in oldbreaks[1:]:
                if prevbrk <= val < nextbrk:
                    breaks.insert(i, val)
                    break
                else:
                    prevbrk = nextbrk
                i += 1
    
    return breaks

def split(items, breaks, key=None, exclude=None, minval=None, maxval=None, **kwargs):
    """
    Splits a list of items into n non-overlapping classes based on the
    specified algorithm. Values are either the items themselves or
    a value extracted from the item using the key function. 

    Args:

    - **items**: The list of items or values to classify.
    - **breaks**: List of custom break values, or the name of the algorithm to use.
        Valid names are:
        - histogram (alias for equal)
        - equal
        - quantile
        - pretty
        - stdev
        - natural
        - headtail
        - log (base-10, uses offset to handle 0s but not negative numbers)
    - **key** (optional): Function used to extract value from each item, defaults to None and treats item itself as the value.
    - **extrabreaks** (optional): Force insert additional break points. These are added to the original breakpoints,
        so if the classification resulted in 5 groupings, and you insert 2 additional break values, the final classification
        will contain 7 groupings. 
    - **classes** (optional): The number of classes to group the items into. Needed for some break types but not others. 
    - **exclude** (optional): A list of values defining which values to exclude.
    - **minval** (optional): Sets the lower value boundary for the classification groupings, ignoring values below this threshold.
    - **maxval** (optional): Sets the upper value boundary for the classification groupings, ignoring values above this threshold.
    - **kwargs** (optional): Depending on the breaks algorithm used, any remaining kwargs are passed to the algorithm function.
        The algorithm functions and their arguments can be found in `classypie.breaks`.

    Returns:

    - Iterates over the range groupings, each time yielding a 2-tuple of the group (its min-max value range) and a list of the
        items belonging to that group. 
    """

    # ensure values are numeric
    def forcenumber(val):
        try:
            val = float(val)
            return val
        except:
            return None

    # sort and get key
    if key:
        keywrap = lambda x: forcenumber(key(x))
    else:
        keywrap = forcenumber
        
    items = (item for item in items if keywrap(item) is not None)
    if exclude is not None:
        if not isinstance(exclude, (list,tuple)): exclude = [exclude]
        items = (item for item in items if keywrap(item) not in exclude)
    if minval is not None: items = (item for item in items if keywrap(item) >= minval)
    if maxval is not None: items = (item for item in items if keywrap(item) <= maxval)
    items = sorted(items, key=keywrap)
    values = [keywrap(item) for item in items]

    # if not custom specified, get break values from algorithm name
    if isinstance(breaks, bytes):
        func = _breaks.__dict__[breaks]
        breaks = func(values, **kwargs)
    else:
        # custom specified breakpoints
        breaks = list(breaks)

    breaks_gen = (brk for brk in breaks)
    loopdict = dict()
    loopdict["prevbrk"] = next(breaks_gen)
    loopdict["nextbrk"] = next(breaks_gen)

    def find_class(item, loopdict=loopdict):
        val = keywrap(item)
        
##        while eval(bytes(val)) > eval(bytes(loopdict["nextbrk"])):
##            loopdict["prevbrk"] = loopdict["nextbrk"]
##            loopdict["nextbrk"] = next(breaks_gen)
##        if eval(bytes(loopdict["prevbrk"])) <= eval(bytes(val)) <= eval(bytes(loopdict["nextbrk"])):
##            return loopdict["prevbrk"],loopdict["nextbrk"]
        
##        if eval(bytes(val)) < loopdict["prevbrk"]:
##            # value lower than first class
##            return None
##        else:
##            while not (eval(bytes(loopdict["prevbrk"])) <= eval(bytes(val)) <= eval(bytes(loopdict["nextbrk"]))):
##                print eval(bytes(loopdict["prevbrk"])) , eval(bytes(val)) , eval(bytes(loopdict["nextbrk"]))
##                # increment breaks until value is between
##                loopdict["prevbrk"] = loopdict["nextbrk"]
##                loopdict["nextbrk"] = next(breaks_gen, None)
##                if loopdict["nextbrk"] == None:
##                    return None
##            # supposedly in between, so test and return class range
##            if eval(bytes(loopdict["prevbrk"])) <= eval(bytes(val)) < eval(bytes(loopdict["nextbrk"])):
##                return loopdict["prevbrk"],loopdict["nextbrk"]

        prevbrk = breaks[0]
        for i,nextbrk in enumerate(breaks[1:]):
            ###print val,i+1,len(breaks)-1
            if eval(bytes(val)) < eval(bytes(prevbrk)):
                return None
            elif eval(bytes(prevbrk)) <= eval(bytes(val)) < eval(bytes(nextbrk)):
                return prevbrk,nextbrk
            elif eval(bytes(prevbrk)) == eval(bytes(val)) == eval(bytes(nextbrk)):
                return prevbrk,nextbrk
            elif i+1==len(breaks)-1 and eval(bytes(val)) <= eval(bytes(nextbrk)):
                return prevbrk,nextbrk
            prevbrk = nextbrk
        else:
            return None

    for valrange,members in itertools.groupby(items, key=find_class):
        if valrange is not None:
            yield valrange, list(members)

def unique(items, key=None, only=None, exclude=None):
    """
    Bins all same values together, so all bins are unique.
    Only for ints or text values.

    Args:

    - **items**: The list of items or values to classify.
    - **key** (optional): Function used to extract value from each item, defaults to None and treats item itself as the value.
    - **only** (optional): A list of values defining which values to include. 
    - **exclude** (optional): A list of values defining which values to exclude. Does not apply if `only` is already specified.
    """
    
    # sort and get key
    if key:
        pass
    else:
        key = lambda x: x

    if only:
        items = (item for item in items if key(item) in only)
    elif exclude:
        items = (item for item in items if key(item) not in exclude)

    items = sorted(items, key=key)

    for uniq,members in itertools.groupby(items, key=key):
        yield uniq, list(members)

    # maybe add remaining groups if none?
    # ... 

def membership(items, ranges, key=None):
    """
    Groups can be overlapping/nonexclusive and are based on custom ranges.
    This means that each item or value can be part of multiple group ranges. 

    Args:

    - **items**: The list of items or values to classify.
    - **ranges**: A list of min-max tuples defining the upper and lower bounds of each group membership.
    - **key** (optional): Function used to extract value from each item, defaults to None and treats item itself as the value.

    Returns:

    - Iterates over the range groupings, each time yielding a 2-tuple of the group (its min-max value range) and a list of the
        items belonging to that group. 
    """
    ###
    if not key:
        key = lambda x: x
    ###
    for _min,_max in ranges:
        valitems = ((key(item),item) for item in items)
        members = [item for val,item in valitems if val >= _min and val <= _max]
        yield (_min,_max), members

def rescale(items, newmin, newmax, key=None, only=None, exclude=None):
    """
    Iterates over all items, along with a new value for each.
    The new value is the item value rescaled to range from newmin to newmax.

    Args:

    - **items**: The list of items or values to rescale.
    - **newmin**: The new minimum which the lowest item value will be rescaled to.
    - **newmax**: The new maximum which the highest item value will be rescaled to.
    - **key** (optional): Function used to extract value from each item, defaults to None and treats item itself as the value.
    - **only** (optional): A list of values defining which values to include. 
    - **exclude** (optional): A list of values defining which values to exclude. Does not apply if `only` is already specified.

    Returns:

    - Iterates over the input items, each time yielding a tuple of the original item along with the new rescaled value. 
    """
    # ensure values are numeric
    def forcenumber(val):
        try:
            val = float(val)
            return val
        except:
            return None

    # sort and get key
    if key:
        keywrap = lambda x: forcenumber(key(x))
    else:
        keywrap = forcenumber

    pairs = ((item,keywrap(item)) for item in items)
    pairs = ((item,val) for item,val in pairs if val is not None)

    if only:
        pairs = ((item,val) for item,val in pairs if val in only)
    elif exclude:
        pairs = ((item,val) for item,val in pairs if val not in exclude)

    items,values = zip(*pairs)

    oldmin, oldmax = min(values), max(values)

    def _lerp(val, oldfrom, oldto, newfrom, newto):
        oldrange = oldto - oldfrom
        relval = (val - oldfrom) / float(oldrange)
        newrange = newto - newfrom
        newval = newfrom + newrange * relval
        return newval

    # determine appropriate interp func for either sequenes or single values

    if oldmin == oldmax:
        # special case, only one value, return max newval
        def newval(val):
            return newmax
    elif hasattr(newmin, "__iter__") and hasattr(newmax, "__iter__"):
        # tuples of eg colors
        if len(newmin) != len(newmax):
            raise Exception("If newmin/newmax are sequences they must both have the same length")
        def newval(val):
            return [_lerp(val, oldmin, oldmax, ifromval, itoval)
                        for ifromval,itoval in zip(newmin,newmax)]
    else:
        def newval(val):
            return _lerp(val, oldmin, oldmax, newmin, newmax)

    for item,val in zip(items, values):
        nv = newval(val)
        yield item, nv
    
    






