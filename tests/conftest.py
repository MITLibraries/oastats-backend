# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

import pytest


@pytest.fixture
def cfg():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'fixtures/test-config.yml')


@pytest.fixture
def apache_req():
    return '1.2.3.4 - - [31/Jan/2013:23:58:51 -0500] "GET /openaccess-disseminate/1721.1/22774 HTTP/1.1" 200 6865 "-" "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2"'
