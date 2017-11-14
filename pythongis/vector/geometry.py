
from shapely.geometry import shape
from shapely.prepared import prep

from .geography import Geography

class Geometry(object):
    def __init__(self, obj, **kwargs):
        # stored internally as shapely
        if isinstance(obj, dict):
            self._shapely_data = obj # keep geojson as is, dont convert to shapely until needed
        elif kwargs:
            self._shapely_data = kwargs # keep geojson as is, dont convert to shapely until needed
        elif "shapely" in type(obj):
            self._shapely_data = obj
        elif isinstance(obj, Geometry):
            self._shapely_data = obj._shapely_data
        else:
            raise Exception()

        self._prepped_data = None

    @property
    def _shapely(self):
        'shapely object is needed, converted from geojson if needed'
        if isinstance(self._shapely_data, dict):
            self._shapely_data = shape(self._shapely_data)
        return self._shapely_data

    @property
    def _prepped(self):
        'prepared geometry for faster ops, created if needed'
        if not self._prepped_data:
            self._prepped_data = prep(self._shapely)
        return self._prepped_data

    @property
    def __geo_interface__(self):
        if isinstance(self._shapely_data, dict):
            # if shapely not created yet, return directly from geojson
            return self._shapely_data
        else:
            return self._shapely_data.__geo_interface__

    @property
    def type(self):
        return self.__geo_interface__["type"]

    @property
    def coordinates(self):
        return self.__geo_interface__["coordinates"]

    @property
    def geoms(self):
        for geoj in self.__geo_interface__["geometries"]:
            yield Geometry(geoj)

    @property
    def is_empty(self):
        return True if not self._shapely_data else self._shapely.is_empty

    # calculations

    def area(self, geodetic=False):
        if geodetic:
            geog = Geography(self.__geo_interface__)
            return geog.area
        else:
            return self._shapely.area

    def length(self, geodetic=False):
        if geodetic:
            geog = Geography(self.__geo_interface__)
            return geog.length
        else:
            return self._shapely.length

    def distance(self, other, geodetic=False):
        if geodetic:
            geog = Geography(self.__geo_interface__)
            other = Geography(other.__geo_interface__)
            return geog.distance(other)
        else:
            other = Geometry(other)
            return self._shapely.distance(other)

    # tests
    # TODO: Maybe implement batch ops via prepped, or should that be handled higher up...?

    def intersects(self, other):
        return self._shapely.intersects(other._shapely)

    def disjoint(self, other):
        return self._shapely.disjoint(other._shapely)

    def touches(self, other):
        return self._shapely.touches(other._shapely)

    # modify

    def walk(self):
        pass

    def line_to(self):
        pass

    def buffer(self, distance, resolution=100, geodetic=False):
        if geodetic:
            geog = Geography(self.__geo_interface__)
            buff = geog.buffer(distance, resolution)
            return Geometry(buff.__geo_interface__)
        else:
            return self._shapely.buffer(distance, resolution)

    def intersection(self, other):
        return self._shapely.intersection(other._shapely)

    def union(self, other):
        return self._shapely.union(other._shapely)

    def difference(self, other):
        return self._shapely.difference(other._shapely)








    
