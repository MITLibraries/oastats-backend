import logging
import sys

# Configure which fields from the Apache log will be retained and what field
# they will be mapped to in the final JSON object.
APACHE_FIELD_MAPPINGS = {
    'remote_host': 'ip_address',
    'time_received': 'time',
    'request_first_line': 'request',
    'status': 'status',
    'request_header_referer': 'referer',
    'request_header_user_agent': 'user_agent',
    'response_bytes_clf': 'filesize',
}

# Should be a tuple with either host and port, MongoDB URI, or empty
# ex: ('localhost', 27017,) or ('mongodb://localhost:27017',) remember the trailing comma!
MONGO_CONNECTION = ('localhost', 27017,)
MONGO_DB = 'oastats'
MONGO_COLLECTION = 'requests'

# Location of the GeoIP database
GEOIP_DB = 'tests/fixtures/GeoLite2-Country.mmdb'

DSPACE_IDENTITY_SERVICE = 'http://www.example.com'

# Configure logging for the application
log = logging.getLogger('pipeline')
log.addHandler(logging.StreamHandler(sys.stderr))
log.setLevel(logging.WARNING)
