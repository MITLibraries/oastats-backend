# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import sys
import csv
from operator import itemgetter
from itertools import groupby


def load_identities(fp):
    dialect = csv.Sniffer().sniff(fp.read(1024))
    fp.seek(0)
    data = csv.DictReader(fp, dialect=dialect)
    sdata = sorted(data, key=itemgetter('URI'))
    return groupby(sdata, itemgetter('URI'))


def main(filename):
    with open(filename, 'rbU') as fp:
        for handle, identities in load_identities(fp):
            record = {'handle': handle, 'ids': []}
            for identity in identities:
                record['ids'].append({
                    'name': identity['Author'],
                    'mitid': identity.get('MIT ID', "")
                })
            print(json.dumps(record))


if __name__ == '__main__':
    main(sys.argv[1])
