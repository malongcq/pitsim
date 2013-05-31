# Haversine formula
# http://www.platoscave.net/blog/2009/oct/5/calculate-distance-latitude-longitude-python/

import math

Equator_Radius = 6378137
Polar_Radius = 6356752

def distance(origin, destination, radius=6371000):
    lat1, lon1 = origin
    lat2, lon2 = destination
    
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d