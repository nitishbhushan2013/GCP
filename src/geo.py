import geoip2.database
from geoip2.errors import AddressNotFoundError

GEOIP_DB_PATH = "geo_data/GeoLite2-City.mmdb"
_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        _reader = geoip2.database.Reader(GEOIP_DB_PATH)
    return _reader


def get_client_ip(request) -> str:
    """Cloud Run's load balancer sets X-Forwarded-For with the real client
    IP first in the comma-separated list. Falls back to request.client.host
    for local testing, where no proxy header is present."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def resolve_location(ip: str) -> dict:
    """Resolves an IP to coarse city/region/country via the local GeoLite2
    database - no network call, no raw IP persisted by the caller."""
    try:
        response = _get_reader().city(ip)
        return {
            "city": response.city.name,
            "region": response.subdivisions.most_specific.name if response.subdivisions else None,
            "country": response.country.name,
        }
    except (AddressNotFoundError, ValueError):
        # Private/loopback IPs (local testing) and malformed addresses
        # resolve to nothing rather than raising - logging must never
        # break the actual /query response.
        return {"city": None, "region": None, "country": None}