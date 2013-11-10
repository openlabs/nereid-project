# -*- coding: utf-8 -*-
"""
    test_company

    TestCompany

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
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

    def get_template_source(self, name):
        """
        Return templates
        """
        self.templates = {
            'login.jinja': '',
        }
        return self.templates.get(name)

    def test_0010_is_project_admin(self):
        """
        Tests if project is added by nereid user
        """

        with Transaction().start(DB_NAME, USER, CONTEXT):

            currency, = self.Currency.create([{
                'name': 'US Dollar',
                'code': 'USD',
                'symbol': '$',
            }])
            company_party, = self.Party.create([{
                'name': 'Openlabs',
            }])
            company, = self.Company.create([{
                'party': company_party.id,
                'currency': currency.id,
            }])
            party1, = self.Party.create([{
                'name': 'Non registered user',
            }])

            # Create guest user
            guest_user, = self.NereidUser.create([{
                'party': party1.id,
                'display_name': 'Guest User',
                'email': 'guest@openlabs.co.in',
                'password': 'password',
                'company': company.id,
            }])

            party2, = self.Party.create([{
                'name': 'Registered User1',
            }])
            registered_user1, = self.NereidUser.create([{
                'party': party2.id,
                'display_name': 'Registered User',
                'email': 'email@example.com',
                'password': 'password',
                'company': company.id,
            }])

            # Create nereid project site
            url_map, = self.URLMap.search([], limit=1)
            en_us, = self.Language.search([('code', '=', 'en_US')])
            self.locale_en_us, = self.Locale.create([{
                'code': 'en_US',
                'language': en_us.id,
                'currency': currency.id,
            }])
            nereid_project_website, = self.Website.create([{
                'name': 'localhost',
                'url_map': url_map.id,
                'company': company.id,
                'application_user': USER,
                'default_locale': self.locale_en_us.id,
                'guest_user': guest_user.id,
            }])
            self.Company.write([company], {
                'project_admins': [('add', [registered_user1.id])],
            })

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }

            app = self.get_app()
            with app.test_client() as c:
                rv = c.post('/login', data=login_data)
                self.assertEqual(rv.status_code, 302)

                # Assert project admin.
                self.assertEqual(
                    nereid_project_website.company.project_admins[0],
                    registered_user1
                )


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
