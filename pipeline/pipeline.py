# -*- coding: utf-8 -*-
from __future__ import absolute_import
from functools import partial, reduce
import logging
import re


import arrow
from geoip2.errors import AddressNotFoundError
import pycountry
import requests

from pipeline.cache import region


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


logger = logging.getLogger(__name__)


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


def to_iso_date(date):
    dt = arrow.get(date, 'DD/MMM/YYYY:HH:mm:ss Z')
    return dt.isoformat()


def to_country(ip_address, reader):
    alpha2 = get_alpha2_code(ip_address, reader)
    if alpha2 in ('XA', 'XS', 'XX'):
        return 'XXX'
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
    for request in requests:
        try:
            dt = to_iso_date(request.get('time'))
            request['time'] = dt
            yield request
        except arrow.parser.ParserError as e:
            logger.warn(e)


def add_country(requests, reader):
    for request in requests:
        try:
            ccode = to_country(request.get('remote_host'), reader)
            request['country'] = ccode
            yield request
        except (ValueError, KeyError) as e:
            logger.warn(e)


@region.cache_on_arguments()
def get_bitstream(handle, svc_url, session):
    r = session.get(svc_url, params={'handle': handle})
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        logger.warn(e)
        return None
    return r.json()


def add_identities(requests, svc_url, session):
    for request in requests:
        handle = request['request_url'].split("/", 2).pop()
        data = get_bitstream(handle, svc_url, session)
        if data and data.get('success'):
            request['dlcs'] = data.get('departments')
            request['handle'] = data.get('uri')
            request['title'] = data.get('title')
            request['authors'] = [author for authors in
                                  data.get('ids', []) for author in authors]
            yield request


def construct_pipeline(session, reader, dspace, dates):
    _add_country = partial(add_country, reader=reader)
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


def quote_field(field):
    quotable = (',', '"', '\n', '\r')
    value = field.replace('"', '""')
    if any([s in value for s in quotable]) or value == '\.':
        value = '"{}"'.format(value)
    return value


def to_csv(request):
    row = [quote_field(field) for field in request]
    return ','.join(row)
