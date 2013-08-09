# -*- coding: utf-8 -*-
"""
    __init__

    Test Suite

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""

from tests.test_company import TestCompany
from tests.test_project import TestNereidProject
from tests.test_task import TestTask

import unittest
import trytond.tests.test_tryton
from trytond.backend.sqlite.database import Database as SQLiteDatabase


def doctest_dropdb(test):
    '''
    Remove sqlite memory database
    '''
    database = SQLiteDatabase().connect()
    cursor = database.cursor(autocommit=True)
    try:
        database.drop(cursor, ':memory:')
        cursor.commit()
    finally:
        cursor.close()


def suite():
    """
    Define suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestCompany),
        unittest.TestLoader().loadTestsFromTestCase(TestNereidProject),
        unittest.TestLoader().loadTestsFromTestCase(TestTask),
    ])
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
