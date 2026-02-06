from __future__ import annotations

import logging
import reverse_geocoder as rg

# Suppress verbose logging from reverse_geocoder on import
logging.getLogger("reverse_geocoder").setLevel(logging.ERROR)

def get_country_code(lat: float, lon: float) -> str | None:
    """
    Returns 2-letter country code (ISO 3166-1 alpha-2) for given coordinates.
    Uses offline K-D tree (fast, ~20MB memory).
    Example: (35.68, 139.76) -> 'JP'
    """
    if lat is None or lon is None:
        return None
    
    try:
        # mode=1 means single result
        results = rg.search((lat, lon), mode=1)
        if results:
            return results[0].get("cc")
    except Exception:
        return None
    
    return None