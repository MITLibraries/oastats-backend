import geoip2.database
from geoip2.errors import AddressNotFoundError
import pycountry
import arrow
from conf import settings
from .decorators import memoize

reader = geoip2.database.Reader(settings.GEOIP_DB)

@memoize
def get_alpha2_code(ip):
    try:
        res = reader.country(ip)
    except AddressNotFoundError:
        return 'XX'
    if res.country.iso_code is not None:
        return res.country.iso_code
    if res.traits.is_anonymous_proxy:
        return 'XA'
    if res.traits.is_satellite_provider:
        return 'XS'
    return 'XX'

def get_alpha3_code(alpha2):
    country = pycountry.countries.get(alpha2=alpha2)
    return country.alpha3

def add_country(request):
    """Add ISO 3166-1 alpha-3 code to country field of request dict."""
    ip = request.get('ip_address')
    alpha2 = get_alpha2_code(ip)
    if alpha2 in ('XA', 'XS', 'XX'):
        request['country'] = 'XXX'
    else:
        alpha3 = get_alpha3_code(alpha2)
        request['country'] = alpha3
    return request

def str_to_dt(request):
    """Convert Apache timestamp to datetime object."""
    t = arrow.get(request['time'], '[DD/MMM/YYYY:HH:mm:ss Z]')
    request['time'] = t.datetime
    return request

def req_to_url(request):
    """Convert Apache request string to URL."""
    url = request['request'].split()[1]
    request['request'] = url
    return request
