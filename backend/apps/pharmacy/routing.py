"""Route a prescription to the nearest MHS-affiliated pharmacy."""
from __future__ import annotations

import math

from apps.clinics.models import Pharmacy


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_pharmacy(patient_profile=None, fallback_city: str | None = None) -> Pharmacy | None:
    qs = Pharmacy.objects.filter(is_mhs_affiliated=True)
    if not qs.exists():
        return None

    lat = getattr(patient_profile, "latitude", None)
    lon = getattr(patient_profile, "longitude", None)
    if lat is not None and lon is not None:
        ranked = sorted(
            (p for p in qs if p.latitude is not None and p.longitude is not None),
            key=lambda p: _haversine_km(lat, lon, p.latitude, p.longitude),
        )
        if ranked:
            return ranked[0]

    city = fallback_city or getattr(patient_profile, "address", "") or ""
    for p in qs:
        if p.city and p.city.lower() in city.lower():
            return p
    return qs.first()
