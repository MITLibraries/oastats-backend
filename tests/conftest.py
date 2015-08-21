# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os


current_dir = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault('OASTATS_SETTINGS',
                      os.path.join(current_dir, 'fixtures', 'settings.py'))
