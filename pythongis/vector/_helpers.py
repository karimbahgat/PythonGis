
import itertools, math

def _pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)

def vincenty_distance(point1, point2, miles=False, a=6378137, b=6356752.314245, f=1/298.257223563, MILES_PER_KILOMETER=0.621371, MAX_ITERATIONS=200, CONVERGENCE_THRESHOLD=1e-12):
    """
    Vincenty's formula (inverse method) to calculate the distance (in
    kilometers or miles) between two points on the surface of a spheroid
 
    NOTE: Taken entirely from Maurycyp's Vincenty package.
    https://github.com/maurycyp/vincenty/blob/master/vincenty/__init__.py
 
    Doctests:
    >>> vincenty((0.0, 0.0), (0.0, 0.0))  # coincident points
    0.0
    >>> vincenty((0.0, 0.0), (0.0, 1.0))
    111.319491
    >>> vincenty((0.0, 0.0), (1.0, 0.0))
    110.574389
    >>> vincenty((0.0, 0.0), (0.5, 179.5))  # slow convergence
    19936.288579
    >>> vincenty((0.0, 0.0), (0.5, 179.7))  # failure to converge
    >>> boston = (42.3541165, -71.0693514)
    >>> newyork = (40.7791472, -73.9680804)
    >>> vincenty(boston, newyork)
    298.396057
    >>> vincenty(boston, newyork, miles=True)
    185.414657
    """
 
    # short-circuit coincident points
    if point1[0] == point2[0] and point1[1] == point2[1]:
        return 0.0
 
    U1 = math.atan((1 - f) * math.tan(math.radians(point1[0])))
    U2 = math.atan((1 - f) * math.tan(math.radians(point2[0])))
    L = math.radians(point2[1] - point1[1])
    Lambda = L
 
    sinU1 = math.sin(U1)
    cosU1 = math.cos(U1)
    sinU2 = math.sin(U2)
    cosU2 = math.cos(U2)
 
    for iteration in range(MAX_ITERATIONS):
        sinLambda = math.sin(Lambda)
        cosLambda = math.cos(Lambda)
        sinSigma = math.sqrt((cosU2 * sinLambda) ** 2 +
                             (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) ** 2)
        if sinSigma == 0:
            return 0.0  # coincident points
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
        sigma = math.atan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha ** 2
        try:
            cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cosSqAlpha
        except ZeroDivisionError:
            cos2SigmaM = 0
        C = f / 16 * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha))
        LambdaPrev = Lambda
        Lambda = L + (1 - C) * f * sinAlpha * (sigma + C * sinSigma *
                                               (cos2SigmaM + C * cosSigma *
                                                (-1 + 2 * cos2SigmaM ** 2)))
        if abs(Lambda - LambdaPrev) < CONVERGENCE_THRESHOLD:
            break  # successful convergence
    else:
        return None  # failure to converge
 
    uSq = cosSqAlpha * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)))
    B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
    deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (cosSigma *
                 (-1 + 2 * cos2SigmaM ** 2) - B / 6 * cos2SigmaM *
                 (-3 + 4 * sinSigma ** 2) * (-3 + 4 * cos2SigmaM ** 2)))
    s = b * A * (sigma - deltaSigma)
 
    s /= 1000  # meters to kilometers
    if miles:
        s *= MILES_PER_KILOMETER  # kilometers to miles
 
    return round(s, 6)
 
def geodetic_length(geometry):
    
    def _handle(geometry):
        if "Point" in geometry["type"]:
            return 0.0
 
        elif geometry["type"] == "LineString":
            length = sum((vincenty_distance(p1,p2)
                          for p1,p2 in _pairwise(geometry["coordinates"]))
                         )
            return length
 
        elif geometry["type"] == "MultiLineString":
            length = sum((vincenty_distance(p1,p2)
                          for line in geometry["coordinates"]
                          for p1,p2 in _pairwise(line))
                         )
            return length
         
        else:
            raise Exception("Geodetic length not yet implemented for Polygons")
 
    if geometry["type"] == "GeometryCollection":
        length = sum((_handle(geom) for geom in geometry["geometries"]))
        return length
 
    else:
        length = _handle(geometry)
        return length


def great_circle_path(point1, point2, segments):
    # http://gis.stackexchange.com/questions/47/what-tools-in-python-are-available-for-doing-great-circle-distance-line-creati
    ptlon1,ptlat1 = point1
    ptlon2,ptlat2 = point2

    numberofsegments = segments
    onelessthansegments = numberofsegments - 1
    fractionalincrement = (1.0/onelessthansegments)

    ptlon1_radians = math.radians(ptlon1)
    ptlat1_radians = math.radians(ptlat1)
    ptlon2_radians = math.radians(ptlon2)
    ptlat2_radians = math.radians(ptlat2)

    distance_radians=2*math.asin(math.sqrt(math.pow((math.sin((ptlat1_radians-ptlat2_radians)/2)),2) + math.cos(ptlat1_radians)*math.cos(ptlat2_radians)*math.pow((math.sin((ptlon1_radians-ptlon2_radians)/2)),2)))
    # 6371.009 represents the mean radius of the earth
    # shortest path distance
    distance_km = 6371.009 * distance_radians

    mylats = []
    mylons = []

    # write the starting coordinates
    mylats.append([])
    mylons.append([])
    mylats[0] = ptlat1
    mylons[0] = ptlon1 

    f = fractionalincrement
    icounter = 1
    while icounter < onelessthansegments:
        icountmin1 = icounter - 1
        mylats.append([])
        mylons.append([])
        # f is expressed as a fraction along the route from point 1 to point 2
        sin_dist_rad = math.sin(distance_radians)
        if sin_dist_rad == 0:
            return [point1,point2] # hack to avoid zerodiv
        A=math.sin((1-f)*distance_radians)/sin_dist_rad
        B=math.sin(f*distance_radians)/sin_dist_rad
        x = A*math.cos(ptlat1_radians)*math.cos(ptlon1_radians) + B*math.cos(ptlat2_radians)*math.cos(ptlon2_radians)
        y = A*math.cos(ptlat1_radians)*math.sin(ptlon1_radians) +  B*math.cos(ptlat2_radians)*math.sin(ptlon2_radians)
        z = A*math.sin(ptlat1_radians) + B*math.sin(ptlat2_radians)
        newlat=math.atan2(z,math.sqrt(math.pow(x,2)+math.pow(y,2)))
        newlon=math.atan2(y,x)
        newlat_degrees = math.degrees(newlat)
        newlon_degrees = math.degrees(newlon)
        mylats[icounter] = newlat_degrees
        mylons[icounter] = newlon_degrees
        icounter += 1
        f = f + fractionalincrement

    # write the ending coordinates
    mylats.append([])
    mylons.append([])
    mylats[onelessthansegments] = ptlat2
    mylons[onelessthansegments] = ptlon2

    return zip(mylons,mylats)
