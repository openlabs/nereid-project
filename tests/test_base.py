# -*- coding: utf-8 -*-
"""
    test_project

    TestProject

    :copyright: (c) 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import smtplib

from trytond.config import CONFIG
CONFIG.options['data_path'] = '.'
CONFIG['smtp_from'] = 'test@openlabs.co.in'
from minimock import Mock

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, USER
from nereid.testing import NereidTestCase

smtplib.SMTP = Mock('smtplib.SMTP')
smtplib.SMTP.mock_returns = Mock('smtp_connection')


class TestBase(NereidTestCase):
    '''
    Creates default values to be used by test cases
    '''

    def setUp(self):
        """
        Set up data used in the tests.
        this method is called before each test function execution.
        """
        trytond.tests.test_tryton.install_module('nereid_project')
        self.ActivityAllowedModel = POOL.get('nereid.activity.allowed_model')

        self.Work = POOL.get('timesheet.work')
        self.Model = POOL.get('ir.model')
        self.Project = POOL.get('project.work')
        self.Company = POOL.get('company.company')
        self.Employee = POOL.get('company.employee')
        self.Currency = POOL.get('currency.currency')
        self.Language = POOL.get('ir.lang')
        self.Website = POOL.get('nereid.website')
        self.NereidUser = POOL.get('nereid.user')
        self.URLMap = POOL.get('nereid.url_map')
        self.Party = POOL.get('party.party')
        self.User = POOL.get('res.user')
        self.Action = POOL.get('ir.action')
        self.TimesheetLine = POOL.get('timesheet.line')
        self.Tag = POOL.get('project.work.tag')
        self.History = POOL.get('project.work.history')
        self.ProjectInvitation = POOL.get('project.work.invitation')
        self.Attachment = POOL.get('ir.attachment')
        self.Permission = POOL.get('nereid.permission')
        self.TaskUsers = POOL.get('project.work-nereid.user')
        self.Activity = POOL.get('nereid.activity')
        self.Locale = POOL.get('nereid.website.locale')
        self.xhr_header = [
            ('X-Requested-With', 'XMLHttpRequest'),
        ]
        self.Configuration = POOL.get('project.configuration')
        self.ProjectWorkCommit = POOL.get('project.work.commit')

        self.templates = {
            'login.jinja': '{{ get_flashed_messages()|safe }}',
            'project/project.jinja': '{{ project.rec_name }}',
            'project/home.jinja': '{{ projects|length }}',
            'project/timesheet.jinja': '{{ employees|length }}',
            'project/global-timesheet.jinja': '{{ employees|length }}',
            'project/global-gantt.jinja': '{{ employees|length }}',
            'project/files.jinja':
                '{{ project.children[0].attachments|length }}',
            'project/permissions.jinja': '{{ invitations|length }}',
            'project/plan.jinja': '{{  }}',
            'project/compare-performance.jinja': '{{ employees|length }}',
            'project/emails/text_content.jinja': '',
            'project/emails/html_content.jinja': '',
            'project/emails/invite_2_project_text.html': '',
            'project/emails/inform_addition_2_project_text.html': '',
            'login.jinja': '{{ get_flashed_messages()|safe }}',
            'project/comment.jinja': '',
            'project/emails/text_content.jinja': '',
            'project/emails/html_content.jinja': '',
            'project/task.jinja': '{{ task.id }}',
            'project/comment.jinja': '',
            'project/tasks-by-employee.jinja': '',
            'project/project-task-list.jinja': '{{ tasks|length }}',
            '_helpers.jinja': '',
            'registration.jinja': '',
        }

    def create_defaults(self):
        """
        Setup the defaults
        """
        currency, = self.Currency.create([{
            'name': 'US Dollar',
            'code': 'USD',
            'symbol': '$',
        }])
        company_party, = self.Party.create([{
            'name': 'Openlabs',
        }])
        self.company, = self.Company.create([{
            'party': company_party.id,
            'currency': currency.id,
        }])

        party1, party2, party3, party4, party5, party6 = self.Party.create([{
            'name': 'Non registered user',
        }, {
            'name': 'Registered User1',
        }, {
            'name': 'Registered User2',
        }, {
            'name': 'Registered User3',
        }, {
            'name': 'Project Admin User',
        }, {
            'name': 'Project Manager',
        }])

        # Create Employee
        employee1, employee2 = self.Employee.create([{
            'company': self.company.id,
            'party': party2.id,
        }, {
            'company': self.company.id,
            'party': party3.id,
        }])

        # Create guest user, and 3 registered user
        self.guest_user, self.reg_user1 = self.NereidUser.create([{
            'party': party1.id,
            'display_name': 'Guest User',
            'email': 'guest@openlabs.co.in',
            'password': 'password',
            'company': self.company.id,
        }, {
            'party': party2.id,
            'display_name': 'Registered User1',
            'email': 'email@reg_user1.com',
            'password': 'password',
            'company': self.company.id,
            'employee': employee1.id,
        }])

        self.reg_user2, self.reg_user3 = self.NereidUser.create([
            {
                'party': party3.id,
                'display_name': 'Registered User2',
                'email': 'email@reg_user2.com',
                'password': 'password',
                'company': self.company.id,
                'employee': employee2.id,
            }, {
                'party': party4.id,
                'display_name': 'Registered User3',
                'email': 'email@reg_user3.com',
                'password': 'password',
                'company': self.company.id,
            }
        ])

        self.Company.write([self.company], {
            'employees': [('add', [employee1.id])],
        })
        self.user1, self.user2 = self.User.create([
            {
                'name': 'res_user1',
                'login': 'res_user1',
                'password': '1234',
                'main_company': self.company.id,
                'company': self.company.id,
            }, {
                'name': 'res_user2',
                'login': 'res_user2',
                'password': '5678',
            }
        ])

        self.User.write(
            self.User.search([]), {
                'main_company': self.company.id,
                'company': self.company.id,
            }
        )
        self.actor_party, = self.Party.create([{
            'name': 'Actor Party',
        }])

        self.nereid_user_actor, = self.NereidUser.create([{
            'party': self.actor_party.id,
            'company': self.company.id,
            'display_name': self.actor_party.name,
            'email': 'actor@email.com',
        }])

        # Create nereid project site
        en_us, = self.Language.search([('code', '=', 'en_US')])

        self.locale_en_us, = self.Locale.create([{
            'code': 'en_US',
            'language': en_us.id,
            'currency': currency.id,
        }])
        self.nereid_project_website, = self.Website.create([{
            'name': 'localhost',
            'company': self.company.id,
            'application_user': USER,
            'default_locale': self.locale_en_us.id,
            'guest_user': self.guest_user.id,
        }])

        # Nereid Permission
        admin_permission = self.Permission.search([
            ('value', '=', 'project.admin')
        ])

        manager_permission = self.Permission.search([
            ('value', '=', 'project.manager')
        ])
        self.project_admin_user, = self.NereidUser.create([{
            'party': party5.id,
            'display_name': 'Project Admin User',
            'email': 'admin@project.com',
            'password': 'password',
            'company': self.company.id,
        }])

        self.project_manager_user, = self.NereidUser.create([{
            'party': party6.id,
            'display_name': 'Project Manager User',
            'email': 'manager@project.com',
            'password': 'password',
            'company': self.company.id,
        }])
        self.Permission.write(
            admin_permission, {
                'nereid_users': [('add', [self.project_admin_user.id])]
            }
        )

        self.Permission.write(
            manager_permission, {
                'nereid_users': [('add', [self.project_manager_user.id])]
            }
        )

        config = self.Configuration(1)
        config.git_webhook_secret = 'somesecret'
        config.save()

    def create_defaults_for_project(self):
        '''
        Create default project, tasks and tags
        '''
        self.create_defaults()

        # Create project
        self.work1, = self.Work.create([{
            'name': 'ABC',
            'company': self.company.id,
        }])
        self.project1, = self.Project.create([{
            'work': self.work1.id,
            'type': 'project',
            'state': 'opened',
        }])

        # Create Tags
        self.tag1, = self.Tag.create([{
            'name': 'tag1',
            'color': 'color1',
            'project': self.project1.id
        }])
        self.tag2, = self.Tag.create([{
            'name': 'tag2',
            'color': 'color2',
            'project': self.project1.id
        }])
        self.tag3, = self.Tag.create([{
            'name': 'tag3',
            'color': 'color3',
            'project': self.project1.id
        }])
        self.work2, = self.Work.create([{
            'name': 'ABC_task',
            'company': self.company.id,
        }])
        self.task1, = self.Project.create([{
            'work': self.work2.id,
            'comment': 'task_desc',
            'parent': self.project1.id,
        }])
        self.work3, = self.Work.create([{
            'name': 'ABC_task2',
            'company': self.company.id,
        }])
        self.task2, = self.Project.create([{
            'work': self.work3.id,
            'comment': 'task_desc',
            'parent': self.project1.id,
        }])
        self.work4, = self.Work.create([{
            'name': 'ABC_task3',
            'company': self.company.id,
        }])
        self.task3, = self.Project.create([{
            'work': self.work4.id,
            'comment': 'task_desc',
            'parent': self.project1.id,
        }])

        self.Project.write(
            [self.task1.parent],
            {
                'members': [
                    ('create', [{
                        'user': self.reg_user2.id,
                    }, {
                        'user': self.reg_user1.id
                    }])
                ]
            }
        )

        # Add tag2 to task
        self.Project.write(
            [self.task1, self.task2],
            {'tags': [('add', [self.tag2.id])]}
        )

    def login(self, client, username, password, assert_=True):
        """
        Tries to login.

        .. note::
            This method MUST be called within a context

        :param client: Instance of the test client
        :param username: The username, usually email
        :param password: The password to login
        :param assert_: Boolean value to indicate if the login has to be
                        ensured. If the login failed an assertion error would
                        be raised
        """
        rv = client.post(
            '/login', data={
                'email': username,
                'password': password,
            }
        )
        if assert_:
            self.assertEqual(rv.status_code, 302)
        return rv

    def logout(self, client, assert_=True):
        """
        logout current user

        .. note::
            This method MUST be called within a context
        """
        rv = client.get('/logout')
        if assert_:
            self.assertEqual(rv.status_code, 302)
        return rv
