#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    setup

    :copyright: (c) 2012-2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""


from setuptools import setup
import re
import os
import ConfigParser


def get_files(root):
    for dirname, dirnames, filenames in os.walk(root):
        for filename in filenames:
            yield os.path.join(dirname, filename)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

config = ConfigParser.ConfigParser()
config.readfp(open('tryton.cfg'))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
major_version, minor_version, _ = info.get('version', '0.0.1').split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)

requires = [
    'raven',
    'blinker',
    'simplejson',
    'trytond >= 3.0.3, < 3.1',
]
for dep in info.get('depends', []):
    if not re.match(r'(ir|res|webdav)(\W|$)', dep):
        requires.append(
            'trytond_%s >= %s.%s, < %s.%s' %
            (dep, major_version, minor_version, major_version,
                minor_version + 1)
        )
requires.append(
    'trytond >= %s.%s, < %s.%s' %
    (major_version, minor_version, major_version, minor_version + 1)
)

setup(
    name='trytond_nereid_project',
    version=info.get('version', '0.0.1'),
    description='Tryton Nereid Web based Project Management',
    author='Openlabs Technologies & Consulting (P) Limited',
    author_email='info@openlabs.co.in',
    url='http://www.openlabs.co.in/',
    package_dir={'trytond.modules.nereid_project': '.'},
    packages=[
        'trytond.modules.nereid_project',
        'trytond.modules.nereid_project.tests'
    ],
    package_data={
        'trytond.modules.nereid_project': info.get('xml', [])
        + info.get('translation', []) + ['tryton.cfg']
        + list(get_files("templates/"))
        + list(get_files("static/")),
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Office/Business',
    ],
    license='GPL-3',
    install_requires=requires,
    tests_require=['minimock'],
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    nereid_project = trytond.modules.nereid_project
    """,
    test_suite='tests',
    test_loader='trytond.test_loader:Loader',
)
