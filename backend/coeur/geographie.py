"""Distances a vol d'oiseau, calculees en local (decision D-25).

Aucun appel reseau : la formule de haversine tient en dix lignes et repond en
microsecondes. La distance a vol d'oiseau n'est pas la distance routiere —
c'est une limite assumee, suffisante pour des bandes de frais (D-11) et pour
decider si une boutique Express entre dans le rayon d'un client (D-09).
"""
from math import asin, cos, radians, sin, sqrt

RAYON_TERRE_KM = 6371.0


def distance_km(lat1, lon1, lat2, lon2):
    """Distance entre deux points, en kilometres. None si une valeur manque."""
    if None in (lat1, lon1, lat2, lon2):
        return None

    lat1, lon1, lat2, lon2 = (radians(float(v)) for v in (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return round(2 * RAYON_TERRE_KM * asin(sqrt(a)), 2)
