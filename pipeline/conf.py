# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os


class Settings(object):

    def __init__(self):
        try:
            import importlib.machinery
            loader = importlib.machinery.SourceFileLoader('pipeline.settings',
                                                          os.environ['OASTATS_SETTINGS'])
            settings_module = loader.load_module('pipeline.settings')
        except ImportError:
            import imp
            settings_module = imp.load_source('pipeline.settings',
                                              os.environ['OASTATS_SETTINGS'])
        self.SETTINGS = SettingsContainer(settings_module)

    def __getattr__(self, name):
        return getattr(self.SETTINGS, name)


class SettingsContainer(object):

    def __init__(self, settings):
        for setting in dir(settings):
            if setting == setting.upper():
                value = getattr(settings, setting)
                setattr(self, setting, value)


settings = Settings()
