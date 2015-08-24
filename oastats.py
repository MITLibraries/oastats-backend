import os

current_dir = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault("OASTATS_SETTINGS",
                      os.path.join(current_dir, "settings.py"))

import fileinput
import sys
from pipeline.conf import settings
from pipeline import process
from pipeline.load_json import get_collection, insert
import logging
import apachelog
import requests

log = logging.getLogger("pipeline")
req_log = logging.getLogger("req_log")

collection = get_collection(settings.MONGO_DB,
                            settings.MONGO_COLLECTION,
                            settings.MONGO_CONNECTION)

def main():
    """Parse stream of requests and insert into MongoDB collection.

    This script will accept input from either stdin or one or more files as
    arguments. Two loggers control logging--one general purpose logger for the
    application and one for logging requests that fail to make it through the
    pipeline. The latter is configured to route different kinds of failures to
    different streams as configured. The failed requests will be logged
    unmodified, as they entered the pipeline, to make later attempts at
    processing easier.

    Failure to send any requests through the pipeline will result in an exit
    status of 1.
    """
    req_buffer = []

    for line in fileinput.input():
        try:
            request = process(line, settings)
        except apachelog.ApacheLogParserError:
            # log unparseable requests
            req_log.error(line.strip(), extra={'err_type': 'REQUEST_ERROR'})
            continue
        except requests.exceptions.RequestException:
            req_log.error(line.strip(), extra={'err_type': 'DSPACE_ERROR'})
            continue
        except Exception, e:
            log.error(e, extra={'inputfile': fileinput.filename(),
                                'inputline': fileinput.filelineno()})
            continue
        if request:
            req_buffer.append(request)
        if len(req_buffer) > 999:
            insert(collection, req_buffer)
            req_buffer = []
    if req_buffer:
        insert(collection, req_buffer)
    if not fileinput.lineno():
        sys.exit("No requests to process")
    log.info("{0} requests processed".format(fileinput.lineno()))


if __name__ == '__main__':
    main()
