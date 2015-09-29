# -*- coding: utf-8 -*-
"""
OAStats Pipeline
"""

import io
from setuptools import find_packages, setup


with io.open('LICENSE') as f:
    license = f.read()


setup(
    name='oastats-pipeline',
    version='0.1.0',
    description='Generate download statistics for the Open Access collection',
    long_description=__doc__,
    url='https://github.com/MITLibraries/oastats-backend',
    license=license,
    author='Mike Graves',
    author_email='mgraves@mit.edu',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'PyYAML',
        'apache-log-parser',
        'arrow',
        'click',
        'futures',
        'geoip2',
        'maxminddb',
        'pycountry',
        'pymongo',
        'pysolr',
        'python-dateutil',
        'requests',
        'six',
        'ua-parser',
        'user-agents',
    ],
    extras_require={
        ':python_version=="2.7"': ['ipaddr'],
    },
    entry_points={
        'console_scripts': [
            'oastats = pipeline.cli:main',
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ]
)
