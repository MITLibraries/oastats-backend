# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re
from functools import partial, reduce

import arrow
from dogpile.cache import make_region
from geoip2.errors import AddressNotFoundError
import pycountry


field_names = ('remote_host', 'remote_logname', 'remote_user', 'time',
               'request_method', 'request_url', 'request_http_version',
               'status', 'bytes', 'referer', 'user_agent')
pattern = re.compile(r'(\S+) (\S+) (\S+) \[(.*?)\] "(\S+) '
                     r'(/openaccess-disseminate/[0-9.]+/[0-9]+) (\S+)" (\S+) '
                     r'(\S+) "(.*?)" "(.*)"')
bots_startswith = ("java", "python", "libwww", "lwp-trivial", "htdig", "xenu",
                   "tineye", "yacy", "pycurl", "linkwalker", "ocelli")
bots_contain = ('bot', 'crawler', 'spider', 'findlinks', 'feedfetcher',
                'slurp', 'sensis', 'jeeves', 'nutch', 'harvest', 'larbin',
                'archiver', 'ichiro', 'scrubby', 'silk', 'referee',
                'webcollages', 'store')


def key_gen(ns, fn, **kwargs):
    fname = fn.__name__

    def generate_key(*arg):
        return fname + "_" + str(arg[0])
    return generate_key


region = make_region(
    function_key_generator=key_gen).configure('dogpile.cache.memory')


class Compose(object):
    def __init__(self, f, g):
        self.f = f
        self.g = g

    def __call__(self, *args):
        return self.f(self.g(*args))


def compose(*funcs):
    return reduce(Compose, funcs)


def get_alpha2_code(ip, database):
    try:
        res = database.country(ip)
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


def map_field(requests, field, func, new_field=None):
    new_field = new_field or field
    for r in requests:
        r[new_field] = func(r[field])
        yield r


def to_iso_date(date):
    dt = arrow.get(date, 'DD/MMM/YYYY:HH:mm:ss Z')
    return dt.isoformat()


def to_country(ip_address, reader):
    alpha2 = get_alpha2_code(ip_address, reader)
    if alpha2 in ('XA', 'XS', 'XX'):
        return 'XXX'
    else:
        return get_alpha3_code(alpha2)


def filter_by_date(lines, dates=None):
    for line in lines:
        if not dates:
            yield line
        elif any([d in line for d in dates]):
            yield line


def filter_by_method(lines):
    for line in lines:
        if ' "GET ' in line:
            yield line


def filter_by_ip(lines, ip_addresses=('127.0.0.1', '18.7.27.25', '::1')):
    for line in lines:
        if not any([line.startswith(ip) for ip in ip_addresses]):
            yield line


def parse_into_dict(lines):
    for line in lines:
        match = pattern.match(line)
        if match:
            yield dict(zip(field_names, match.groups()))


def filter_by_status(requests):
    for request in requests:
        if request['status'] == '200':
            yield request


def filter_bots(requests):
    for request in requests:
        ua = request['user_agent'].lower()
        if not ua.startswith(bots_startswith) and \
           not any([s in ua for s in bots_contain]):
            yield request


def convert_datetime(requests):
    return map_field(requests, 'time', to_iso_date)


def add_country(requests, func):
    return map_field(requests, 'remote_host', func, new_field='country')


@region.cache_on_arguments()
def get_bitstream(handle, svc_url, session):
    r = session.get(svc_url, params={'handle': handle})
    return r.json()


def add_identities(requests, svc_url, session):
    for request in requests:
        handle = request['request_url'].split("/", 2).pop()
        data = get_bitstream(handle, svc_url, session)
        if data.get('success'):
            request['dlcs'] = data.get('departments')
            request['handle'] = data.get('uri')
            request['title'] = data.get('title')
            request['authors'] = [author for authors in
                                  data.get('ids', []) for author in authors]
            yield request


def construct_pipeline(session, reader, dspace, dates):
    _to_country = partial(to_country, reader=reader)
    _add_country = partial(add_country, func=_to_country)
    _filter_by_date = partial(filter_by_date, dates=dates)
    _add_identities = partial(add_identities, svc_url=dspace, session=session)

    return compose(_add_identities,
                   _add_country,
                   convert_datetime,
                   filter_bots,
                   filter_by_status,
                   parse_into_dict,
                   filter_by_ip,
                   _filter_by_date,
                   filter_by_method,)
