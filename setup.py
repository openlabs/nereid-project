#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    setup

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""


from setuptools import setup, Command
import re
import os
import unittest
import sys
import time
import ConfigParser


def get_files(root):
    for dirname, dirnames, filenames in os.walk(root):
        for filename in filenames:
            yield os.path.join(dirname, filename)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class PostgresTest(Command):
    """
    Run the tests on Postgres.
    """
    description = "Run tests on Postgresql"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(
                self.distribution.install_requires
            )
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)

        from trytond.config import CONFIG
        CONFIG['db_type'] = 'postgresql'
        CONFIG['db_host'] = 'localhost'
        CONFIG['db_port'] = 5432
        CONFIG['db_user'] = 'postgres'

        from trytond import backend
        import trytond.tests.test_tryton

        # Set the db_type again because test_tryton writes this to sqlite
        # again
        CONFIG['db_type'] = 'postgresql'

        trytond.tests.test_tryton.DB_NAME = 'test_' + str(int(time.time()))
        from trytond.tests.test_tryton import DB_NAME
        trytond.tests.test_tryton.DB = backend.get('Database')(DB_NAME)
        from trytond.pool import Pool
        Pool.test = True
        trytond.tests.test_tryton.POOL = Pool(DB_NAME)

        from tests import suite
        test_result = unittest.TextTestRunner(verbosity=3).run(suite())

        if test_result.wasSuccessful():
            sys.exit(0)
        sys.exit(-1)


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
        + info.get('translation', []) + ['tryton.cfg', 'view/*.xml']
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
    cmdclass={'test_on_postgres': PostgresTest}
)
