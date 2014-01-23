# -*- coding: utf-8 -*-
"""
    test_project

    TestProject

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest
import json
import smtplib
from StringIO import StringIO

from trytond.config import CONFIG
CONFIG.options['data_path'] = '.'
CONFIG['smtp_from'] = 'test@openlabs.co.in'
from minimock import Mock

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction
#from trytond.error import UserError
from nereid.testing import NereidTestCase

smtplib.SMTP = Mock('smtplib.SMTP')
smtplib.SMTP.mock_returns = Mock('smtp_connection')


class TestNereidProject(NereidTestCase):
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
        self.ProjectUsers = POOL.get('project.work-nereid.user')
        self.Activity = POOL.get('nereid.activity')
        self.Locale = POOL.get('nereid.website.locale')
        self.xhr_header = [
            ('X-Requested-With', 'XMLHttpRequest'),
        ]

        self.templates = {
            'login.jinja': '{{ get_flashed_messages()|safe }}',
            'project/project.jinja': '{{ project.rec_name }}',
            'project/home.jinja': '{{ projects|length }}',
            'project/timesheet.jinja': '{{ employees|length }}',
            'project/files.jinja':
                '{{ project.children[0].attachments|length }}',
            'project/permissions.jinja': '{{ invitations|length }}',
            'project/plan.jinja': '{{  }}',
            'project/compare-performance.jinja': '{{ employees|length }}',
            'project/emails/text_content.jinja': '',
            'project/emails/html_content.jinja': '',
            'project/emails/invite_2_project_text.html': '',
            'project/emails/inform_addition_2_project_text.html': '',
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
        company, = self.Company.create([{
            'party': company_party.id,
            'currency': currency.id,
        }])

        party1, party2, party3, party4 = self.Party.create([{
            'name': 'Non registered user',
        }, {
            'name': 'Registered User',
        }, {
            'name': 'Registered User2',
        }, {
            'name': 'Registered User3',
        }])

        # Create Employee
        employee1, employee2 = self.Employee.create([{
            'company': company.id,
            'party': party2.id,
        }, {
            'company': company.id,
            'party': party3.id,
        }])

        # Create guest user, and 3 registered user
        guest_user, registered_user1, registered_user2, registered_user3, = \
            self.NereidUser.create([{
                'party': party1.id,
                'display_name': 'Guest User',
                'email': 'guest@openlabs.co.in',
                'password': 'password',
                'company': company.id,
            }, {
                'party': party2.id,
                'display_name': 'Registered User1',
                'email': 'email@example.com',
                'password': 'password',
                'company': company.id,
                'employee': employee1.id,
            }, {
                'party': party3.id,
                'display_name': 'Registered User2',
                'email': 'example@example.com',
                'password': 'password',
                'company': company.id,
                'employee': employee2.id,
            }, {
                'party': party4.id,
                'display_name': 'Registered User3',
                'email': 'res_user@example.com',
                'password': 'password',
                'company': company.id,
            }])

        self.Company.write([company], {
            'project_admins': [('add', [registered_user1.id])],
            'employees': [('add', [employee1.id])],
        })
        menu_list = self.Action.search([('usage', '=', 'menu')])
        user1, user2 = self.User.create([
            {
                'name': 'res_user1',
                'login': 'res_user1',
                'password': '1234',
                'menu': menu_list[0].id,
                'main_company': company.id,
                'company': company.id,
            }, {
                'name': 'res_user2',
                'login': 'res_user2',
                'password': '5678',
                'menu': menu_list[0].id,
            }
        ])
        actor_party, = self.Party.create([{
            'name': 'Actor Party',
        }])

        self.nereid_user_actor, = self.NereidUser.create([{
            'party': actor_party.id,
            'company': company.id,
            'display_name': actor_party.name,
            'email': 'actor@email.com',
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

        # Nereid Permission
        permission = self.Permission.search([
            ('value', '=', 'project.admin')
        ])
        self.Permission.write(
            permission,
            {
                'nereid_users': [
                    ('add', [registered_user1.id, registered_user2.id])
                ]
            }
        )

        return {
            'company': company,
            'party1': party1,
            'party2': party2,
            'nereid_project_website': nereid_project_website,
            'registered_user1': registered_user1,
            'registered_user2': registered_user2,
            'registered_user3': registered_user3,
            'guest_user': guest_user,
            'employee1': employee1,
            'employee2': employee2,
            'user1': user1,
            'user2': user2,
        }

    def test_0010_create_project_when_user_is_not_admin(self):
        """
        Tests for the creation of project when nereid user is not admin, this
        shows a flash message and would not create project
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                login_data = {
                    'email': 'example@example.com',
                    'password': 'password',
                }

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    response = c.post('/login', data=login_data)
                    self.assertEqual(
                        response.location, 'http://localhost/'
                    )
                    self.assertEqual(response.status_code, 302)

                    # Get flash message for logged in user
                    response = c.get('/login')
                    self.assertTrue(
                        u'You are now logged in. Welcome Registered User2' in
                            response.data
                    )

                    # Create project when user is not admin
                    response = c.post('/project/-new', data={
                        'name': 'ABC',
                        'type': 'project',
                        'company': data['company'].id,
                        'parent': False,
                        'state': 'opened',
                    })
                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Sorry! You are not allowed to create new projects.' +
                        ' Contact your project admin for the same.' in
                        response.data
                    )

    def test_0020_check_logout(self):
        """
        Test logout successfully
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                login_data = {
                    'email': 'example@example.com',
                    'password': 'password',
                }

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    response = c.post('/login', data=login_data)
                    self.assertEqual(
                        response.location, 'http://localhost/'
                    )
                    self.assertEqual(response.status_code, 302)
                    # Logout user
                    response = c.get('/logout')
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(
                        response.location, 'http://localhost/'
                    )

                    response = c.get('/login')
                    self.assertTrue(
                        u'You have been logged out successfully. Thanks for' +
                        ' visiting us' in response.data
                    )
                    self.assertEqual(response.status_code, 200)

    def test_0030_create_project_when_user_is_admin(self):
        """
        Create project when nereid user is admin
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/me')
                self.assertEqual(rv.status_code, 302)

                with Transaction().set_context(
                        {'company': data['company'].id}):
                    # User Login
                    response = c.post('/login', data={
                        'email': 'email@example.com',
                        'password': 'password',
                    })
                    response = c.get('/login')
                    self.assertTrue(
                        u'You are now logged in. Welcome Registered User1' in
                        response.data
                    )

                    # Length of project before creating is zero as no project
                    # is added yet
                    self.assertEqual(len(self.Project.search([])), 0)

                    # Create project when nereid user is admin
                    response = c.post('/project/-new', data={
                        'name': 'ABC',
                        'type': 'project',
                        'company': data['company'].id,
                        'parent': False,
                        'state': 'opened',
                    })
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(
                        response.location, 'http://localhost/project-1'
                    )

                    # Check Flash message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Project successfully created.' in response.data
                    )

                    # Length of project is now one as one project is created
                    self.assertEqual(len(self.Project.search([])), 1)

                    # Create project with get request when nereid user is admin
                    # , it will show flash message, and won't create project
                    response = c.get('/project/-new', data={
                        'name': 'ABC',
                        'type': 'project',
                        'company': data['company'].id,
                        'parent': False,
                        'state': 'opened',
                    })
                    self.assertEqual(response.status_code, 302)
                    response = c.get('/login')
                    self.assertTrue(
                        u'Could not create project. Try again.' in
                        response.data
                    )

    def test_0040_render_project(self):
        """
        Tests names of all projects rendered
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            with app.test_client() as c:

                login_data = {
                    'email': 'email@example.com',
                    'password': 'password',
                }

                with Transaction().set_context(
                        {'company': data['company'].id}):
                    response = c.post('/login', data=login_data)
                    self.assertEqual(response.status_code, 302)

                    response = c.get('/project-%d' % project.id)
                    self.assertEqual(response.status_code, 200)

                    # Checks if renders the same project that is created
                    self.assertEqual(response.data, 'ABC')

    def test_0050_get_projects_on_home_when_user_is_admin(self):
        """
        Tests if project is shown to admin user on projects home page
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work1, work2 = self.Work.create([
                {
                    'name': 'ABC',
                    'company': data['company'].id,
                },
                {
                    'name': 'PQR',
                    'company': data['company'].id,
                }
            ])
            project1, project2 = self.Project.create([
                {
                    'work': work1.id,
                    'type': 'project',
                    'state': 'opened',
                },
                {
                    'work': work2.id,
                    'type': 'project',
                    'state': 'opened',
                }
            ])
            self.assertEqual(len(self.Project.search([])), 2)
            with app.test_client() as c:

                login_data = {
                    'email': 'email@example.com',
                    'password': 'password',
                }

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    response = c.post('/login', data=login_data)
                    self.assertEqual(response.status_code, 302)

                    response = c.get('/projects')
                    self.assertEqual(response.status_code, 200)

                    # Total project 2 shown to admin
                    self.assertEqual(response.data, '2')

    def test_0060_get_projects_on_home_when_user_is_not_admin(self):
        """
        Tests if all projects on home is not shown to nereid user who is not
        admin, only those projects are shown for which the nereid user is
        participant
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work = self.Work.create([
                {
                    'name': 'ABC',
                    'company': data['company'].id,
                },
                {
                    'name': 'PQR',
                    'company': data['company'].id,
                }
            ])
            project1, project2 = self.Project.create([
                {
                    'work': work[0].id,
                    'type': 'project',
                    'state': 'opened',
                },
                {
                    'work': work[1].id,
                    'type': 'project',
                    'state': 'opened',
                }
            ])
            self.assertEqual(len(self.Project.search([])), 2)

            self.Project.write(
                [project1],
                {
                    'participants': [
                        ('add', [data['registered_user3'].id])
                    ]
                }
            )

            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'res_user@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    response = c.get('/projects')

                    # Total project shown is 1 as nereid user is a participant
                    # for that project only
                    self.assertEqual(response.data, '1')

    def test_0070_create_tag_nereid_user_is_admin(self):
        """
        Tests for creating tag for specific project when nereid user is admin
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    response = c.post(
                        '/project-%d/tag/-new' % project.id,
                        data={
                            'name': 'TagProject',
                            'color': 'Black',
                        }
                    )

                    # Redirecting back to refer page
                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Successfully created tag' in response.data
                    )

                    # Tests for creating tag for specific project with get
                    # request
                    response = c.get(
                        '/project-%d/tag/-new' % project.id,
                        data={
                            'name': 'TagProject',
                            'color': 'Black',
                            'project': project.id,
                        }
                    )

                    # Redirecting back to refer page
                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Could not create tag. Try Again' in response.data
                    )

    def test_0080_create_tag_nereid_user_is_not_admin(self):
        """
        Tests for creating tag for specific project if not admin, it won't
        create tag
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            # For project nereid user should be participant of that project
            self.Project.write(
                [project],
                {
                    'participants': [('add', [data['registered_user2'].id])]
                }
            )

            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'example@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    response = c.post(
                        '/project-%d/tag/-new' % project.id,
                        data={
                            'name': 'TagProject',
                            'color': 'Black',
                        }
                    )

                    # Redirecting back to refer page
                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Sorry! You are not allowed to create new tags.' +
                        ' Contact your project admin for the same.' in
                        response.data
                    )

    def test_0090_delete_tag_when_nereid_user_is_not_admin(self):
        """
        Tests for deleting tag for project when nereid user is not admin
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            # For project nereid user should be participant of that project
            self.Project.write(
                [project],
                {
                    'participants': [('add', [data['registered_user2'].id])]
                }
            )

            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'example@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    # Create Tags
                    tag, = self.Tag.create([{
                        'name': 'tag1',
                        'color': 'color1',
                        'project': project.id
                    }])
                    response = c.post('/tag-%d/-delete' % tag.id)

                    # Redirecting back to refer page
                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Sorry! You are not allowed to delete tags. Contact' +
                        ' your project admin for the same.' in response.data
                    )

    def test_0100_delete_tag_when_nereid_user_is_admin(self):
        """
        Tests for deleting tag for project when nereid user is admin
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    # Create Tags
                    tag, = self.Tag.create([{
                        'name': 'tag',
                        'color': 'color',
                        'project': project.id
                    }])

                    response = c.post(
                        '/tag-%d/-delete' % tag.id,
                        headers=self.xhr_header,
                    )

                    # Checking json {"success": true}
                    self.assertTrue(json.loads(response.data)['success'])

                    # Rendering back to next page
                    self.assertEqual(response.status_code, 200)

                    # Tests for deleting tag for project with get request
                    response = c.get('/tag-%d/-delete' % tag.id)

                    # Redirecting back to refer page
                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Could not delete tag! Try again.' in response.data
                    )

    def test_0110_compare_performance(self):
        """
        Tests number of employees
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):

                    response = c.get('/projects/-compare-performance')
                    self.assertTrue(response.status_code, 200)

                    # Checks number of employees renders
                    self.assertEqual(response.data, '2')

    def test_0120_upload_files(self):
        """
        Checks that file is uploaded, renders and downloaded successfully
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])
            work1, work2 = self.Work.create([{
                'name': 'ABC_task',
                'company': data['company'].id,
            }, {
                'name': 'PQR_task',
                'company': data['company'].id,
            }])
            task1, task2 = self.Project.create([{
                'work': work1.id,
                'comment': 'task_desc',
                'parent': project.id,
                'type': 'task',
            }, {
                'work': work2.id,
                'comment': 'task2',
                'parent': project.id,
                'type': 'task',
            }])

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                # Try uploading files without logging in and
                # there should be a redirect to login page
                response = c.post('/attachment/-upload')
                self.assertEqual(response.status_code, 302)

                # Login success
                response = c.post('/login', data=login_data)
                self.assertEqual(response.location, 'http://localhost/')
                self.assertEqual(response.status_code, 302)

                # Upload file
                response = c.post(
                    '/attachment/-upload',
                    data={
                        'file': (StringIO('testfile contents'), 'test1.txt'),
                        'task': task1.id,
                    },
                    content_type="multipart/form-data"
                )
                self.assertEqual(response.status_code, 302)

                response = c.get('/login')
                self.assertTrue(
                    u'Attachment added to ABC_task' in response.data
                )

                # File 'test1.txt' added successfully in task1
                self.assertEqual(len(self.Attachment.search([])), 1)

                # Add same file to other task
                response = c.post(
                    '/attachment/-upload',
                    data={
                        'file': (StringIO('testfile contents'), 'test1.txt'),
                        'task': task2.id,
                    },
                    content_type="multipart/form-data"
                )
                self.assertEqual(response.status_code, 302)

                response = c.get('/login')
                self.assertTrue(
                    u'Attachment added to PQR_task' in response.data
                )

                # Same file 'test1.txt' added successfully in task2
                self.assertEqual(len(self.Attachment.search([])), 2)

                # Upload same file again
                response = c.post(
                    '/attachment/-upload',
                    data={
                        'file': (StringIO('testfile contents'), 'test1.txt'),
                        'task': task1.id,
                    },
                    content_type="multipart/form-data"
                )
                self.assertEqual(response.status_code, 302)

                # Same file is added successfully
                self.assertEqual(len(self.Attachment.search([])), 3)

                # Add same file content with different file name
                response = c.post(
                    '/attachment/-upload',
                    data={
                        'file': (StringIO('testfile contents'), 'test2.txt'),
                        'task': task1.id,
                    },
                    content_type="multipart/form-data"
                )
                self.assertEqual(response.status_code, 302)

                # 2nd file with same content is added successfully
                response = c.get('/project-%d/-files' % project.id)
                self.assertEqual(response.data, '3')

                # Total file added in attachments
                self.assertEqual(len(self.Attachment.search([])), 4)

    def test_0130_render_files(self):
        """
        Tests rendering of files
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])
            # Add tasks to project
            work1, = self.Work.create([{
                'name': 'ABC_task',
                'company': data['company'].id,
            }])
            task1, = self.Project.create([{
                'work': work1.id,
                'comment': 'task_desc',
                'parent': project.id,
            }])
            attachment, = self.Attachment.create([{
                'name': 'Attachment1',
                'type': 'link',
                'resource': ('project.work', task1.id),
                'description': 'desc1',
            }])

            self.Project.write(
                [task1],
                {'attachments': [('add', [attachment.id])]}
            )

            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):

                    response = c.get('/project-%d/-files' % project.id)
                    self.assertEqual(response.data, '1')

    def test_0140_download_file(self):
        """
        Checks the same file is downloaded
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])
            work1, = self.Work.create([{
                'name': 'ABC_task',
                'company': data['company'].id,
            }])
            task1, = self.Project.create([{
                'work': work1.id,
                'comment': 'task_desc',
                'parent': project.id,
            }])
            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):

                    # Upload file
                    response = c.post(
                        '/attachment/-upload',
                        data={
                            'file': (
                                StringIO('testfile contents'), 'test.txt'
                            ),
                            'task': task1.id,
                        },
                        content_type="multipart/form-data"
                    )
                    self.assertEqual(response.status_code, 302)

                    attachment, = self.Attachment.search([
                        ('name', '=', 'test.txt'),
                        ('resource', '=', 'project.work,%d' % task1.id)
                    ],)

                    # Download file and the file content must be same as
                    # uploaded
                    response = c.get(
                        '/attachment-%d/-download?task=%d' %
                        (attachment.id, task1.id)
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, 'testfile contents')

    def test_0150_project_work_permissions(self):
        """
        Tests permissions for the project
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])
            invitation, = self.ProjectInvitation.create([{
                'email': 'example@example.com',
                'invitation_code': '123',
                'nereid_user': data['registered_user3'].id,
                'project': project.id,
            }])
            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    response = c.get(
                        '/project-%d/-permissions?invitations=%d' %
                        (project.id, invitation.id)
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, '0')

    def test_0160_remove_participants_by_nereid_user(self):
        """
        Checks if removes participant by user who is not admin, it won't
        remove
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            # Add participant to project
            participant, = self.ProjectUsers.create([{
                'project': project.id,
                'user': data['registered_user2'].id,
            }])
            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'res_user@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    response = c.post(
                        '/project-%d/participant-%d/-remove' %
                        (project.id, participant.id)
                    )
                    self.assertEqual(response.status_code, 302)
                    response = c.get('/login')
                    self.assertTrue(
                        'Sorry! You are not allowed to remove participants.' +
                        ' Contact your project admin for the same.' in
                        response.data
                    )

    def test_0170_remove_paricipant_admin(self):
        """
        Checks remove participant by admin
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            # Add participant to project
            participant, = self.ProjectUsers.create([{
                'project': project.id,
                'user': data['registered_user2'].id,
            }])
            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    response = c.post(
                        '/project-%d/participant-%d/-remove' %
                        (project.id, participant.id),
                        headers=self.xhr_header,
                    )

                    # Checking json {"success": true}
                    self.assertTrue(json.loads(response.data)['success'])
                    self.assertEqual(response.status_code, 200)

                    # Checks if remove participant by get request
                    response = c.get(
                        '/project-%d/participant-%d/-remove' %
                        (project.id, participant.id)
                    )

                    self.assertEqual(response.status_code, 302)

                    # Checks Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        'Could not remove participant! Try again.'
                        in response.data
                    )

    def test_0180_remove_invite(self):
        """
        Checks removing inviation by non admin user
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            invitation, = self.ProjectInvitation.create([{
                'email': 'example@example.com',
                'invitation_code': '123',
                'nereid_user': data['registered_user3'].id,
                'project': project.id,
            }])
            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'example@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):
                    response = c.post(
                        '/invitation-%d/-remove' % invitation.id
                    )
                    self.assertEqual(response.status_code, 302)
                    response = c.get('/login')
                    self.assertTrue(
                        u'Sorry! You are not allowed to remove invited ' +
                        'users. Contact your project admin for the same.' in
                        response.data
                    )

                    # Checks by get request
                    response = c.get(
                        '/invitation-%d/-remove' % invitation.id
                    )
                    self.assertEqual(response.status_code, 302)

    def test_0190_resend_invite(self):
        """
        Checks if it resend the invitation
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
            }])

            invitation, = self.ProjectInvitation.create([{
                'email': 'example@example.com',
                'invitation_code': '123',
                'nereid_user': data['registered_user3'].id,
                'project': project.id,
            }])
            with app.test_client() as c:

                # User Login
                response = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                with Transaction().set_context({
                    'company': data['company'].id
                }):

                    response = c.post(
                        '/invitation-%d/-resend' % invitation.id,
                        headers=self.xhr_header,
                    )

                    # Checking json {"success": true}
                    self.assertTrue(json.loads(response.data)['success'])
                    self.assertEqual(response.status_code, 200)

    def test_0190_constraints(self):
        """
        Checks unique constraint on project and nereid user
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': data['company'].id,
            }])

            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'parent': False,
                'state': 'opened',
            }])

            # Add participant to project
            self.ProjectUsers.create([{
                'project': project.id,
                'user': data['registered_user2'].id,
            }])
            self.assertRaises(
                Exception, self.ProjectUsers.create,
                [{
                    'project': project.id,
                    'user': data['registered_user2'].id,
                }]
            )

    def test_0200_stream_with_project(self):
        '''
        Tests that if user is part of project then he must be able to see all
        the activity streams of projects where he is participant
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            data = self.create_defaults()
            app = self.get_app()

            work1, = self.Work.create([{
                'name': 'Test Project1',
                'company': data['company'].id,
            }])
            work2, = self.Work.create([{
                'name': 'Test Project2',
                'company': data['company'].id,
            }])

            project1, = self.Project.create([{
                'work': work1.id,
                'type': 'project',
                'parent': False,
                'state': 'opened',
                'participants': [('set', [data['registered_user1'].id])]
            }])
            project2, = self.Project.create([{
                'work': work2.id,
                'type': 'project',
                'parent': False,
                'state': 'opened',
                'participants': [('set', [data['registered_user2'].id])]
            }])
            project_model, = self.Model.search([
                ('model', '=', 'project.work')
            ])

            # Create activities for project 1 the user is part of
            self.Activity.create([{
                'verb': 'Add project 1',
                'actor': self.nereid_user_actor.id,
                'object_': 'project.work,%s' % project1.id,
                'project': project1.id,
            }])

            self.Activity.create([{
                'verb': 'Add project 1 again',
                'actor': self.nereid_user_actor.id,
                'object_': 'project.work,%s' % project1.id,
                'project': project1.id,
            }])

            # Create activity for project 2
            self.Activity.create([{
                'verb': 'Add project 2',
                'actor': self.nereid_user_actor.id,
                'object_': 'project.work,%s' % project2.id,
                'project': project2.id,
            }])

            with app.test_client() as c:
                # Login Success
                rv = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                self.assertEqual(rv.status_code, 302)

                # Stream after login
                rv = c.get('/user/activity-stream')
                self.assertEqual(rv.status_code, 200)
                rv_json = json.loads(rv.data)

                # There are 2 activities for project-1 and 1 activity for
                # project-2
                # So only 2 activities are returned since user is participant
                # of project-1 only
                self.assertEqual(rv_json['totalItems'], 2)
                self.assertTrue(
                    filter(
                        lambda item: item['verb'] == 'Add project 1',
                        rv_json['items']
                    )
                )
                self.assertTrue(
                    filter(
                        lambda item: item['verb'] == 'Add project 1 again',
                        rv_json['items']
                    )
                )

                # Activity stream for project-2 should not be there
                self.assertFalse(
                    filter(
                        lambda item: item['verb'] == 'Add project 2',
                        rv_json['items']
                    )
                )

    def test_0200_stream_without_project(self):
        '''
        Tests if user is not part of a project then he must be able to see all
        the activity streams created by him
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            data = self.create_defaults()
            app = self.get_app()

            work1, = self.Work.create([{
                'name': 'Test Project1',
                'company': data['company'].id,
            }])
            work2, = self.Work.create([{
                'name': 'Test Project2',
                'company': data['company'].id,
            }])

            project1, = self.Project.create([{
                'work': work1.id,
                'type': 'project',
                'parent': False,
                'state': 'opened',
            }])
            project2, = self.Project.create([{
                'work': work2.id,
                'type': 'project',
                'parent': False,
                'state': 'opened',
                'participants': [('set', [data['registered_user1'].id])]
            }])
            project_model, = self.Model.search([
                ('model', '=', 'project.work')
            ])

            # Activities created by logged-in user
            self.Activity.create([{
                'verb': 'Add project 1',
                'actor': data['registered_user1'].id,
                'object_': 'project.work,%s' % project1.id,
                'project': project1.id,
            }])

            self.Activity.create([{
                'verb': 'Add project 1 again',
                'actor': data['registered_user1'].id,
                'object_': 'project.work,%s' % project2.id,
            }])

            # Create activity for different user
            self.Activity.create([{
                'verb': 'Add project 2',
                'actor': self.nereid_user_actor.id,
                'object_': 'project.work,%s' % project2.id,
            }])

            with app.test_client() as c:
                # Login Success
                rv = c.post('/login', data={
                    'email': 'email@example.com',
                    'password': 'password',
                })
                self.assertEqual(rv.status_code, 302)

                # Stream after login
                rv = c.get('/user/activity-stream')
                self.assertEqual(rv.status_code, 200)
                rv_json = json.loads(rv.data)

                # Only two activities are created by logged-in user
                self.assertEqual(rv_json['totalItems'], 2)
                self.assertTrue(
                    filter(
                        lambda item: item['verb'] == 'Add project 1',
                        rv_json['items']
                    )
                )
                self.assertTrue(
                    filter(
                        lambda item: item['verb'] == 'Add project 1 again',
                        rv_json['items']
                    )
                )

                # Activity stream created by different user should not be there
                self.assertFalse(
                    filter(
                        lambda item: item['verb'] == 'Add project 2',
                        rv_json['items']
                    )
                )


def suite():
    "Nereid test suite"
    test_suite = unittest.TestSuite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestNereidProject)
    )
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
