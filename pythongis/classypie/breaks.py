"""
The actual breakpoint algorithm implementations. Users should not use these
directly, but rather use the higher-level functionality in main.py. 
"""
# original: Carson Farmer
# http://carsonfarmer.com/2010/09/playing-around-with-classification-algorithms-python-and-qgis/
# modified: Karim Bahgat, 2015

from __future__ import division
import math
import random



# Algorithms for value breakpoints

def histogram(values, **kwargs):
    """
    Alias for equal interval.
    """
    return equal(values, **kwargs)

def equal(values, classes=5, interval=None, anchor=None, clip=True, start=None, end=None):
    """
    Equal interval algorithm in Python
    
    Returns breaks based on dividing the range of 'values' into 'classes' parts,
    or by specifying the interval and/or anchorpoint to start the divisioning. 
    """
    #values = sorted(values) # maybe not needed as is already done main.py

    if len(values) == 1:
        # when too few values, just return breakpoints for each unique value, ignoring classes
        return values * 2
    
    # auto detect value range from values if not custom specified
    if start == None:
        _min = min(values)
    else:
        _min = start
    if end == None:
        _max = max(values)
    else:
        _max = end
    
    if interval:
        # interval is custom specified
        if anchor is None:
            start = _min
        else:
            # find the starting point as the first interval that precedes the minimum
            start = anchor
            while start < _min-interval:
                # if lower, then increase up until right before min
                start += interval
            while start > _min:
                # if higher, then decrease until below min
                start -= interval

        # start creating breaks, ensuring to include min and max values
        k = start
        res = []
        while k < _max+interval:
            res.append(k)
            k += interval

        # clip first and last break to min and max
        if clip:
            res[0] = _min
            res[-1] = _max
        
    else:
        # calculate interval based on nr of classes
        unit = (_max - _min) / classes
        res = [_min + k*unit for k in range(classes+1)]

    return res

def log(values, classes=5):
    """
    Log classification algorithm.

    Returns break points at equal intervals of the log10 of input values.
    Handles 0s by adding 1 before log transforming. Negative values will raise Exception.
    """
    # if too few values, just return breakpoints for each unique value, ignoring classes
    if len(values) == 1:
        return values * 2
    
    # log transform values
    logs = [math.log10(v+1) for v in values]

    # create breaks
    minval,maxval = min(logs),max(logs)
    interval = (maxval-minval)/float(classes)
    logbreaks = []
    cur = minval
    while cur <= maxval:
        logbreaks.append(cur)
        cur += interval

    # transform back
    breaks = [(10**log)-1 for log in logbreaks]
    
    return breaks
    
def quantile(values, classes=5):
    """
    Quantile algorithm in Python
    
    Returns values taken at regular intervals from the cumulative 
    distribution function (CDF) of 'values'.
    """

    #values = sorted(values) # maybe not needed as is already done main.py

    # if too few values, just return breakpoints for each unique value, ignoring classes
    if len(values) <= classes:
        return list(values) + [values[-1]]
    
    n = len(values)
    breaks = []
    for i in range(classes):
        q = i / float(classes)
        a = q * n
        aa = int(q * n)
        r = a - aa
        Xq = (1 - r) * values[aa] + r * values[aa+1]
        breaks.append(Xq)
    breaks.append(values[n-1])
    return breaks

def pretty(values, classes=5, start=None, end=None):
    """
    R's pretty algorithm implemented in Python
    Code based on R implementation from 'labeling' R package.
    
    Compute a sequence of about 'n+1' equally spaced 'round' values
    which cover the range of the values in 'values'.  The values are chosen
    so that they are 1, 2 or 5 times a power of 10.

    Returns a number of breaks not necessarily equal to 'classes' using 
    rpretty, but likely to be legible.

    Parameters:
        values : list of input values
        classes     : number of class intervals
    """

    # if too few values, just return breakpoints for each unique value, ignoring classes
    if values and len(values) == 1:
        return values * 2

    # auto detect value range from values if not custom specified
    if start == None:
        dmin = min(values)
    else:
        dmin = start
    if end == None:
        dmax = max(values)
    else:
        dmax = end
        
    # begin
    n = classes
    min_n = int(n / 3) # Nonnegative integer giving the minimal number of intervals
    shrink_sml = 0.75  # Positive numeric by a which a default scale is shrunk 
                                         # in the case when range(x) is very small (usually 0).
    high_u_bias = 1.5  # Non-negative numeric, typically > 1. The interval unit 
                                         # is determined as {1,2,5,10} times b, a power of 10.
                                         # Larger high.u.bias values favor larger units
    u5_bias = 0.5 + 1.5 * high_u_bias
                                         # Non-negative numeric multiplier favoring 
                                         # factor 5 over 2.
    h = high_u_bias
    h5 = u5_bias
    ndiv = n

    dx = dmax - dmin
    if dx == 0 and dmax == 0:
        cell = 1.0
        i_small = True
        U = 1
    else:
        cell = max(abs(dmin), abs(dmax))
        if h5 >= 1.5 * h + 0.5:
            U = 1 + (1.0/(1 + h))
        else:
            U = 1 + (1.5 / (1 + h5))
        i_small = dx < (cell * U * max(1.0, ndiv) * 1e-07 * 3.0)

    if i_small:
        if cell > 10:
            cell = 9 + cell / 10
            cell = cell * shrink_sml
        if min_n > 1:
            cell = cell / min_n
    else:
        cell = dx
        if ndiv > 1:
            cell = cell / ndiv
    if cell < 20 * 1e-07:
        cell = 20 * 1e-07
    
    base = 10.0**math.floor(math.log10(cell))
    unit = base
    if (2 * base) - cell < h * (cell - unit):
        unit = 2.0 * base
        if (5 * base) - cell < h5 * (cell - unit):
            unit = 5.0 * base
            if (10 * base) - cell < h * (cell - unit):
                unit = 10.0 * base
    # Maybe used to correct for the epsilon here??
    ns = math.floor(dmin / unit + 1e-07)
    nu = math.ceil(dmax / unit - 1e-07)

    # Extend the range out beyond the data. Does this ever happen??
    while ns * unit > dmin + (1e-07 * unit):
        ns = ns-1
    while nu * unit < dmax - (1e-07 * unit):
        nu = nu+1
    # If we don't have quite enough labels, extend the range out to make more (these labels are beyond the data :( )
    k = math.floor(0.5 + nu-ns)
    if k < min_n:
        k = min_n - k
        if ns >= 0:
            nu = nu + k / 2
            ns = ns - k / 2 + k % 2
        else:
            ns = ns - k / 2
            nu = nu + k / 2 + k % 2
        ndiv = min_n
    else:
        ndiv = k
    graphmin = ns * unit
    graphmax = nu * unit
    count = int(math.ceil(graphmax - graphmin)/unit)
    res = [graphmin + k*unit for k in range(count+1)]
    if res[0] < dmin:
        res[0] = dmin
    if res[-1] > dmax:
        res[-1] = dmax
    return res

def stdev(values, classes=5):
    """
    Python implementation of the standard deviation class interval algorithm
    as implemented in the 'classInt' package available for 'R'.
    
    Returns breaks based on 'pretty' of the centred and scaled values of 'values',
    and may have a number of classes different from 'classes'.
    """

    # if too few values, just return breakpoints for each unique value, ignoring classes
    if len(values) <= classes:
        return list(values) + [values[-1]]

    sd2 = 0.0
    N = len(values)
    _min = min(values)
    _max = max(values)
    mean = sum(values) / N
    for i in values:
        sd = i - mean
        sd2 += sd * sd
    sd2 = math.sqrt(sd2 / N)
    res = pretty(values=None, classes=5, start=(_min-mean)/sd2, end=(_max-mean)/sd2)
    res2 = [(val*sd2)+mean for val in res]
    return res2

def natural(values, classes=5, maxsize=1000, samples=3):
    """
    Jenks Optimal (Natural Breaks) algorithm implemented in Python.
    The original Python code comes from here:
    http://danieljlewis.org/2010/06/07/jenks-natural-breaks-algorithm-in-python/
    and is based on a JAVA and Fortran code available here:
    https://stat.ethz.ch/pipermail/r-sig-geo/2006-March/000811.html
    
    Returns class breaks such that classes are internally homogeneous while 
    assuring heterogeneity among classes.

    For very large datasets (larger than maxsize), will calculate only on
    subsample to avoid exponential runtimes. Calculated multiple times (samples)
    and takes the average break values for better consistency. Lower and higher
    bounds are kept intact. 
    """

    #values = sorted(values) # maybe not needed as is already done main.py

    # if too few values, just return breakpoints for each unique value, ignoring classes
    if len(values) <= classes:
        return list(values) + [values[-1]]

    def getbreaks(values, classes):
        # the original algorithm by Carson Farmer
        mat1 = []
        for i in range(0,len(values)+1):
            temp = []
            for j in range(0,classes+1):
                temp.append(0)
            mat1.append(temp)
        mat2 = []
        for i in range(0,len(values)+1):
            temp = []
            for j in range(0,classes+1):
                temp.append(0)
            mat2.append(temp)
        for i in range(1,classes+1):
            mat1[1][i] = 1
            mat2[1][i] = 0
            for j in range(2,len(values)+1):
                mat2[j][i] = float('inf')
        v = 0.0
        for l in range(2,len(values)+1):
            s1 = 0.0
            s2 = 0.0
            w = 0.0
            for m in range(1,l+1):
                i3 = l - m + 1
                val = float(values[i3-1])
                s2 += val * val
                s1 += val
                w += 1
                v = s2 - (s1 * s1) / w
                i4 = i3 - 1
                if i4 != 0:
                    for j in range(2,classes+1):
                        if mat2[l][j] >= (v + mat2[i4][j - 1]):
                            mat1[l][j] = i3
                            mat2[l][j] = v + mat2[i4][j - 1]
            mat1[l][1] = 1
            mat2[l][1] = v
        k = len(values)
        kclass = []
        for i in range(0,classes+1):
            kclass.append(0)
        kclass[classes] = float(values[len(values) - 1])
        kclass[0] = float(values[0])
        countNum = classes
        while countNum >= 2:
            id = int((mat1[k][countNum]) - 2)
            kclass[countNum - 1] = values[id]
            k = int((mat1[k][countNum] - 1))
            countNum -= 1
        return kclass

    # Automatic sub sampling for large datasets
    # The idea of using random sampling for large datasets was in the original code. 
    # However, since these samples tend to produce different results,
    # ...to produce more stable results we might as well calculate the
    # ...breaks several times and using the sample means for the final break values.
    
    if len(values) > maxsize:
        allrandomsamples = []
        for _ in range(samples):
            randomsample = sorted(random.sample(values, maxsize))
            
            # include lower and higher bounds to ensure the whole range is considered
            randomsample[0] = values[0] 
            randomsample[-1] = values[-1]
            
            # get sample break
            tempbreaks = getbreaks(randomsample, classes)
            allrandomsamples.append(tempbreaks)
            
        # get average of all sampled break values
        jenksbreaks = [sum(allbreakvalues)/float(len(allbreakvalues))
                       for allbreakvalues in zip(*allrandomsamples)]
        
    else:
        jenksbreaks = getbreaks(values, classes)

    return jenksbreaks

def headtail(values, classes=5):
    """
    New head tails classification scheme,
    claimed to better highlight a few very
    large values than natural breaks.
    See: http://arxiv.org/ftp/arxiv/papers/1209/1209.2801.pdf
    """

    # if too few values, just return breakpoints for each unique value, ignoring classes
    if len(values) == 1:
        return values * 2

    def _mean(values):
        return sum(values)/float(len(values))
    
    def _mbreak(values):
        m = _mean(values)
        head = [v for v in values if v >= m]
        tail = [v for v in values if v < m]
        return head,m,tail

    breaks = []
    head,m,tail = _mbreak(values)
    while len(tail) > len(head):
        breaks.append(m)
        if len(head) > 1:
            head,m,tail = _mbreak(head)
        else:
            break

    # add first and last endpoints
    breaks.insert(0, values[0])
    breaks.append(values[-1])
    
    # merge top breaks until under maxclasses
    if classes and len(breaks) > classes:
        pass
        
    return breaks

##def auto(values, classes=5, **kwargs):
##    raise NotImplementedError()


