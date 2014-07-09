# -*- coding: utf-8 -*-
"""
    test_company

    TestCompany

    :copyright: (c) 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction
from nereid.testing import NereidTestCase


class TestCompany(NereidTestCase):
    '''
    Test Company
    '''
    # pylint: disable-msg=C0103
    # pylint False trigger Using Invalid name

    def setUp(self):
        """
        Set up data used in the tests.
        this method is called before each test function execution.
        """
        trytond.tests.test_tryton.install_module('nereid_project')
        self.Website = POOL.get('nereid.website')
        self.NereidUser = POOL.get('nereid.user')
        self.Currency = POOL.get('currency.currency')
        self.Company = POOL.get('company.company')
        self.Party = POOL.get('party.party')
        self.Employee = POOL.get('company.employee')
        self.URLMap = POOL.get('nereid.url_map')
        self.Language = POOL.get('ir.lang')
        self.Website = POOL.get('nereid.website')
        self.Locale = POOL.get('nereid.website.locale')
        self.Permission = POOL.get('nereid.permission')

    def get_template_source(self, name):
        """
        Return templates
        """
        self.templates = {
            'login.jinja': '',
        }
        return self.templates.get(name)

    def test_0010_check_project_admins(self):
        """
        Tests project admins for the company
        """

        with Transaction().start(DB_NAME, USER, CONTEXT):

            currency, = self.Currency.create([{
                'name': 'US Dollar',
                'code': 'USD',
                'symbol': '$',
            }])
            company_party1, = self.Party.create([{
                'name': 'Openlabs',
            }])

            company_party2, = self.Party.create([{
                'name': 'Openlabs',
            }])
            company1, = self.Company.create([{
                'party': company_party1.id,
                'currency': currency.id,
            }])

            company2, = self.Company.create([{
                'party': company_party2.id,
                'currency': currency.id,
            }])

            party1, party2, party3 = self.Party.create([{
                'name': 'Test User 1',
            }, {
                'name': 'Test User 2',
            }, {
                'name': 'Test Party 3',
            }])

            admin_permission, = self.Permission.search([
                ('value', '=', 'project.admin')
            ])

            # Create user with project admin permission
            user1, = self.NereidUser.create([{
                'party': party1.id,
                'display_name': 'Test user 1',
                'email': 'guest@openlabs.co.in',
                'password': 'password',
                'company': company1.id,
                'permissions': [('set', [admin_permission.id])]
            }])

            # Create user with project admin permission
            user2, = self.NereidUser.create([{
                'party': party2.id,
                'display_name': 'Test user 2',
                'email': 'email@example.com',
                'password': 'password',
                'company': company1.id,
            }])

            # Create user with project admin permission but for some other
            # company
            user3, = self.NereidUser.create([{
                'party': party2.id,
                'display_name': 'Test user 3',
                'email': 'email@example.com',
                'password': 'password',
                'company': company2.id,
                'permissions': [('set', [admin_permission.id])]
            }])

            self.assertTrue(user1 in company1.project_admins)
            self.assertTrue(user2 not in company1.project_admins)
            self.assertTrue(user3 not in company1.project_admins)
            self.assertTrue(user3 in company2.project_admins)

    def test_0010_check_managers(self):
        """
        Tests project admins for the company
        """

        with Transaction().start(DB_NAME, USER, CONTEXT):

            currency, = self.Currency.create([{
                'name': 'US Dollar',
                'code': 'USD',
                'symbol': '$',
            }])
            company_party1, = self.Party.create([{
                'name': 'Openlabs',
            }])

            company_party2, = self.Party.create([{
                'name': 'Openlabs',
            }])
            company1, = self.Company.create([{
                'party': company_party1.id,
                'currency': currency.id,
            }])

            company2, = self.Company.create([{
                'party': company_party2.id,
                'currency': currency.id,
            }])

            party1, party2, party3 = self.Party.create([{
                'name': 'Test User 1',
            }, {
                'name': 'Test User 2',
            }, {
                'name': 'Test Party 3',
            }])

            manager_permission, = self.Permission.search([
                ('value', '=', 'project.manager')
            ])

            # Create user with project manager permission
            user1, = self.NereidUser.create([{
                'party': party1.id,
                'display_name': 'Test user 1',
                'email': 'guest@openlabs.co.in',
                'password': 'password',
                'company': company1.id,
                'permissions': [('set', [manager_permission.id])]
            }])

            # Create user with project manager permission
            user2, = self.NereidUser.create([{
                'party': party2.id,
                'display_name': 'Test user 2',
                'email': 'email@example.com',
                'password': 'password',
                'company': company1.id,
            }])

            # Create user with project manager permission but for some other
            # company
            user3, = self.NereidUser.create([{
                'party': party2.id,
                'display_name': 'Test user 3',
                'email': 'email@example.com',
                'password': 'password',
                'company': company2.id,
                'permissions': [('set', [manager_permission.id])]
            }])

            self.assertTrue(user1 in company1.project_managers)
            self.assertTrue(user2 not in company1.project_managers)
            self.assertTrue(user3 not in company1.project_managers)
            self.assertTrue(user3 in company2.project_managers)


def suite():
    "Nereid test suite"
    test_suite = unittest.TestSuite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestCompany)
    )
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
# pylint: enable-msg=C0103
