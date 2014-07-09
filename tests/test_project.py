# -*- coding: utf-8 -*-
"""
    test_project

    TestProject

    :copyright: (c) 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import urllib
import unittest
import json
import smtplib
from StringIO import StringIO
from werkzeug.exceptions import Forbidden

from trytond.config import CONFIG
CONFIG.options['data_path'] = '.'
CONFIG['smtp_from'] = 'test@openlabs.co.in'
from minimock import Mock

from trytond.tests.test_tryton import DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction

from test_base import TestBase

smtplib.SMTP = Mock('smtplib.SMTP')
smtplib.SMTP.mock_returns = Mock('smtp_connection')


class TestProject(TestBase):
    '''
    Creates default values to be used by test cases
    '''

    def test_0005_registration_using_invitation_code(self):
        """
        Check if user got registered and joined project when invitation
        code is there
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app()

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                        'role': 'admin',
                    }])
                ]
            }])

            invitation, = self.ProjectInvitation.create([{
                'email': 'email@reg_user2.com',
                'invitation_code': '123',
                'project': project.id,
            }])

            with app.test_client() as c:
                response = c.get('/registration')
                self.assertEqual(response.status_code, 200)   # GET Request

                data = {
                    'name': 'Registered User',
                    'email': 'regd_user@openlabs.co.in',
                    'password': 'password',
                    'confirm': 'password',
                }

                self.assertFalse(invitation.nereid_user)
                self.assertFalse(self.Activity.search([]))

                response = c.post(
                    '/registration?invitation_code=123', data=data
                )
                self.assertEqual(response.status_code, 302)

                # Check if invitation has nereid user
                self.assertTrue(invitation.nereid_user)

                # Check if invitation code is none
                self.assertFalse(invitation.invitation_code)

                # Check if same user is added as am member of project
                self.assertTrue(
                    invitation.nereid_user in
                    [m.user for m in invitation.project.members]
                )

                # Check if activity stream is created for same
                self.assertEqual(self.Activity.search([], count=True), 1)

                activity, = self.Activity.search([])
                self.assertEqual(activity.actor, invitation.nereid_user)
                self.assertEqual(activity.verb, 'joined_project')

    def test_0006_registration_without_invitation_code(self):
        """
        Check user registration without invitation code
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app()

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                        'role': 'admin',
                    }])
                ]
            }])

            invitation, = self.ProjectInvitation.create([{
                'email': 'email@reg_user2.com',
                'invitation_code': '123',
                'project': project.id,
            }])

            with app.test_client() as c:
                response = c.get('/registration?invitation_code=123')
                self.assertEqual(response.status_code, 200)   # GET Request

                data = {
                    'name': 'Registered User',
                    'email': 'regd_user@openlabs.co.in',
                    'password': 'password',
                    'confirm': 'password',
                }

                self.assertFalse(invitation.nereid_user)
                response = c.post('/registration', data=data)
                self.assertEqual(response.status_code, 302)

                self.assertFalse(invitation.nereid_user)
                self.assertTrue(invitation.invitation_code)

                response = self.login(
                    c, 'regd_user@openlabs.co.in', 'password', assert_=False
                )
                # Login failed
                self.assertNotEqual(response.status_code, 302)

    def test_0020_check_login_logout(self):
        """
        Test if login and logout works successfully
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                response = self.login(
                    c, self.reg_user2.email, 'password'
                )

                # Get flash message for logged in user
                response = c.get('/login')
                self.assertTrue(
                    u'You are now logged in. Welcome Registered User2'
                    in response.data
                )

                # Logout user
                response = self.logout(c)

                response = c.get('/login')
                self.assertTrue(
                    u'You have been logged out successfully. Thanks for' +
                    ' visiting us' in response.data
                )
                self.assertEqual(response.status_code, 200)

    def test_0010_create_project_when_user_is_not_project_admin(self):
        """
        Tests for the creation of project when nereid user is not project admin
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # Successful login
                response = self.login(c, self.reg_user3.email, 'password')

                # Create project when user is not admin
                response = c.post('/project/-new', data={
                    'name': 'ABC',
                    'type': 'project',
                    'company': self.company.id,
                    'parent': None,
                    'state': 'opened',
                })

                # Permission Denied
                self.assertEqual(response.status_code, 403)

    def test_0030_create_project_when_user_is_project_admin(self):
        """
        Create project when nereid user has project admin permission
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app()

            with app.test_client() as c:
                rv = c.get('/me')
                self.assertEqual(rv.status_code, 302)

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                projects_before_creation = self.Project.search([], count=True)

                # Create project when nereid user is admin
                response = c.post('/project/-new', data={
                    'name': 'ABC',
                    'type': 'project',
                    'company': self.company.id,
                    'parent': None,
                    'state': 'opened',
                })
                project, = self.Project.search([
                    ('work.name', '=', 'ABC')
                ])
                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.location,
                    'http://localhost/project-%d' % project.id
                )
                response = c.get('http://localhost/project-%d' % project.id)
                self.assertEqual(response.status_code, 200)

                # Check Flash message
                response = c.get('/login')
                self.assertTrue(
                    u'Project successfully created.' in response.data
                )

                # Check projects after creating new project
                projects_after_creation = self.Project.search([], count=True)

                # Number of projects must be increased by 1
                self.assertEqual(
                    projects_after_creation, projects_before_creation + 1
                )

                # Create project with get request when nereid user is admin
                # , it will show flash message, and won't create project
                response = c.get('/project/-new', data={
                    'name': 'ABC',
                    'type': 'project',
                    'company': self.company.id,
                    'parent': False,
                    'state': 'opened',
                })
                self.assertEqual(response.status_code, 302)

                # Project is not added so number of projects are same
                self.assertEqual(
                    self.Project.search([], count=True),
                    projects_after_creation
                )
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
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                        'role': 'admin'
                    }])
                ]
            }])

            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                response = c.get('/project-%d' % project.id)
                self.assertEqual(response.status_code, 200)

                # Checks if renders the same project that is created
                self.assertEqual(response.data, 'ABC')

    def test_0050_get_projects_on_home_when_user_is_admin(self):
        """
        Tests if project is shown to admin user on projects home page
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work1, work2 = self.Work.create([
                {
                    'name': 'ABC',
                    'company': self.company.id,
                },
                {
                    'name': 'PQR',
                    'company': self.company.id,
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

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                response = c.get('/projects')
                self.assertEqual(response.status_code, 200)

                # Total project 2 shown to admin
                self.assertEqual(response.data, '2')

                # Check with website home if it redirects to project home
                response = c.get('/')
                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    urllib.unquote(response.location),
                    'http://localhost/projects'
                )

    def test_0060_get_projects_on_home_when_user_is_not_admin(self):
        """
        Tests that non-admin user is allowed to see projects only where he
        he is added as participant
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work = self.Work.create([
                {
                    'name': 'ABC',
                    'company': self.company.id,
                },
                {
                    'name': 'PQR',
                    'company': self.company.id,
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
                [project1], {
                    'members': [
                        ('create', [{
                            'user': self.reg_user3.id
                        }])
                    ]
                }
            )

            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user3.email, 'password')
                response = c.get('/projects')

                # Total project shown is 1 as nereid user is a participant
                # for that project only
                self.assertEqual(response.data, '1')

    def test_0070_create_tag(self):
        """
        Tests that tags can be created by only project admin or admin member of
        the project
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                        'role': 'admin'
                    }, {
                        'user': self.reg_user2.id
                    }])
                ]
            }])

            # Create tag as project admin
            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )
                self.assertTrue(
                    self.project_admin_user.is_admin_of_project(project)
                )
                response = c.post(
                    '/project-%d/tag/-new' % project.id,
                    data={
                        'name': 'TagProject1',
                        'color': 'Blue',
                    }
                )

                # Redirecting back to refer page
                self.assertEqual(response.status_code, 302)

                # Check Flash Message
                response = c.get('/login')
                self.assertTrue(
                    u'Successfully created tag' in response.data
                )

            # Create tag as admin member of the project
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')
                self.assertTrue(self.reg_user1.is_admin_of_project(project))
                response = c.post(
                    '/project-%d/tag/-new' % project.id,
                    data={
                        'name': 'TagProject2',
                        'color': 'Red',
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

            # Create tag as non admin user ( neither project admin nor admin
            # member)
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user2.email, 'password')

                self.assertFalse(
                    self.reg_user2.is_admin_of_project(project)
                )
                response = c.post(
                    '/project-%d/tag/-new' % project.id,
                    data={
                        'name': 'TagProject3',
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

    def test_0090_delete_tags(self):
        """
        Tests that tags can be deleted only if user is
        1. Project Admin
        2. Admin Member of the project
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user2.id
                    }, {
                        'user': self.reg_user1.id,
                        'role': 'admin'
                    }])
                ]
            }])

            # Create Tags
            tag, = self.Tag.create([{
                'name': 'tag1',
                'color': 'color1',
                'project': project.id
            }])

            # 1. Delete tag as non admin user ( neither project admin nor
            # admin member
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user2.email, 'password')

                self.assertFalse(self.reg_user2.is_admin_of_project(project))

                response = c.post('/tag-%d/-delete' % tag.id)

                # Redirecting back to refer page
                self.assertEqual(response.status_code, 302)

                # Check Flash Message
                response = c.get('/login')
                self.assertTrue(
                    u'Sorry! You are not allowed to delete tags. Contact' +
                    ' your project admin for the same.' in response.data
                )

            # 2. Delete tag as admin member
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                self.assertTrue(self.reg_user1.is_admin_of_project(project))
                self.assertEqual(self.Tag.search([], count=True), 1)
                response = c.post(
                    '/tag-%d/-delete' % tag.id, headers=self.xhr_header,
                )

                # Checking json {"success": true}
                self.assertTrue(json.loads(response.data)['success'])
                self.assertEqual(self.Tag.search([], count=True), 0)

                # Rendering back to next page
                self.assertEqual(response.status_code, 200)

            # 2. Delete tag as project admin
            with app.test_client() as c:
                # Create Tags
                tag, = self.Tag.create([{
                    'name': 'tag',
                    'color': 'color',
                    'project': project.id
                }])

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                self.assertTrue(self.reg_user1.is_admin_of_project(project))
                self.assertEqual(self.Tag.search([], count=True), 1)
                response = c.post(
                    '/tag-%d/-delete' % tag.id, headers=self.xhr_header,
                )

                # Checking json {"success": true}
                self.assertTrue(json.loads(response.data)['success'])
                self.assertEqual(self.Tag.search([], count=True), 0)

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
        Tests that only project admin or project manager are allowed to compare
        performance of employees
        """
        # Check with project admin user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                response = c.get('/projects/-compare-performance')
                self.assertTrue(response.status_code, 200)

                # Checks number of employees renders
                self.assertEqual(response.data, '2')

        # Check with project manager user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_manager_user.email, 'password'
                )

                response = c.get('/projects/-compare-performance')
                self.assertTrue(response.status_code, 200)

                # Checks number of employees renders
                self.assertEqual(response.data, '2')

        # Check with non admin and non manager user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                response = c.get('/projects/-compare-performance')
                self.assertTrue(response.status_code, 403)

    def test_0115_global_timesheet_performance(self):
        """
        Tests that only project admin or project manager are allowed to
        check global timesheet of employees
        """
        # Check with project admin user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                response = c.get('/projects/timesheet')
                self.assertTrue(response.status_code, 200)

                # Checks number of employees renders
                self.assertEqual(response.data, '2')

        # Check with project manager user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_manager_user.email, 'password'
                )

                response = c.get('/projects/timesheet')
                self.assertTrue(response.status_code, 200)

                # Checks number of employees renders
                self.assertEqual(response.data, '2')

        # Check with non admin and non manager user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                response = c.get('/projects/timsheet')
                self.assertTrue(response.status_code, 403)

    def test_0116_gantt_data(self):
        """
        Tests that only project admin or project manager are allowed to
        check global gantt data of employees
        """
        # Check with project admin user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                response = c.get('/projects/-gantt')
                self.assertTrue(response.status_code, 200)

                # Checks number of employees renders
                self.assertEqual(response.data, '2')

        # Check with project manager user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_manager_user.email, 'password'
                )
                response = c.get('/projects/-gantt')
                self.assertTrue(response.status_code, 200)

                # Checks number of employees renders
                self.assertEqual(response.data, '2')

        # Check with user who is nether admin nor manager user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                response = c.get('/projects/-gantt')
                self.assertTrue(response.status_code, 403)

    def test_0120_upload_files(self):
        """
        Checks that file is uploaded, renders and downloaded successfully
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                    }])
                ]
            }])
            work1, work2 = self.Work.create([{
                'name': 'ABC_task',
                'company': self.company.id,
            }, {
                'name': 'PQR_task',
                'company': self.company.id,
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

            with app.test_client() as c:
                # Try uploading files without logging in and
                # there should be a redirect to login page
                response = c.post('/attachment/-upload')
                self.assertEqual(response.status_code, 302)

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

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

    def test_0120_upload_file_using_link(self):
        """
        Checks that file is uploaded using link
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                    }])
                ]
            }])
            work1, = self.Work.create([{
                'name': 'ABC_task',
                'company': self.company.id,
            }])
            task1, = self.Project.create([{
                'work': work1.id,
                'comment': 'task_desc',
                'parent': project.id,
                'type': 'task',
            }])

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Upload file
                response = c.post(
                    '/attachment/-upload', data={
                        'url': 'http://www.picturesnew.com'
                        '/media/images/images-background.jpg',
                        'file_type': 'link',
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
                attachment, = self.Attachment.search([])
                self.assertEqual(attachment.name, 'images-background.jpg')
                self.assertEqual(attachment.type, 'link')

    def test_0120_create_attachment_using_file(self):
        """
        Checks if attachment is created (without request context) using file
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                    }])
                ]
            }])
            work1, = self.Work.create([{
                'name': 'ABC_task',
                'company': self.company.id,
            }])
            task, = self.Project.create([{
                'work': work1.id,
                'comment': 'task_desc',
                'parent': project.id,
                'type': 'task',
            }])

            # Create attachment for task
            attachment = task.create_attachment(
                'test1.txt', data='testfile contents'
            )
            self.assertEqual(attachment.name, 'test1.txt')
            self.assertEqual(attachment.type, 'data')

    def test_0120_create_attachment_using_link(self):
        """
        Checks if attachment is created (without request context) using link
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                    }])
                ]
            }])
            work1, = self.Work.create([{
                'name': 'ABC_task',
                'company': self.company.id,
            }])
            task, = self.Project.create([{
                'work': work1.id,
                'comment': 'task_desc',
                'parent': project.id,
                'type': 'task',
            }])

            # Create attachment for task
            attachment = task.create_attachment(
                'images-background.jpg',
                data='http://www.picturesnew.com'
                    '/media/images/images-background.jpg',
                type='link'
            )
            self.assertEqual(attachment.name, 'images-background.jpg')
            self.assertEqual(attachment.type, 'link')

    def test_0130_render_files(self):
        """
        Tests rendering of files
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                    }])
                ]
            }])
            # Add tasks to project
            work1, = self.Work.create([{
                'name': 'ABC_task',
                'company': self.company.id,
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
                response = self.login(c, self.reg_user1.email, 'password')

                response = c.get('/project-%d/-files' % project.id)
                self.assertEqual(response.data, '1')

    def test_0140_download_file(self):
        """
        Checks the same file is downloaded
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                    }])
                ]
            }])
            work1, = self.Work.create([{
                'name': 'ABC_task',
                'company': self.company.id,
            }])
            task1, = self.Project.create([{
                'work': work1.id,
                'comment': 'task_desc',
                'parent': project.id,
            }])
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

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
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                        'role': 'admin',
                    }])
                ]
            }])
            invitation, = self.ProjectInvitation.create([{
                'email': 'email@reg_user2.com',
                'invitation_code': '123',
                'nereid_user': self.reg_user3.id,
                'project': project.id,
            }])

            # Check with admin member
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')
                response = c.get(
                    '/project-%d/-permissions?invitations=%d' %
                    (project.id, invitation.id)
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, '0')

            # Check with non admin member
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user2.email, 'password')
                response = c.get(
                    '/project-%d/-permissions?invitations=%d' %
                    (project.id, invitation.id)
                )
                self.assertEqual(response.status_code, 404)

            # Check with project admin
            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )
                response = c.get(
                    '/project-%d/-permissions?invitations=%d' %
                    (project.id, invitation.id)
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, '0')

    def test_0160_remove_participants(self):
        """
        Checks that participants can only be removed by

        1. Project admin

        2. Admin member of the project
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user2.id
                    }, {
                        'user': self.reg_user3.id,
                    }, {
                        'user': self.reg_user1.id,
                        'role': 'admin',
                    }])
                ]
            }])

            # Check with non admin user
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user3.email, 'password')

                self.assertFalse(self.reg_user3.is_admin_of_project(project))
                response = c.post(
                    '/project-%d/participant-%d/-remove' % (
                        project.id, self.reg_user2.id
                    )
                )

                self.assertEqual(response.status_code, 302)
                response = c.get('/login')
                self.assertTrue(
                    'Sorry! You are not allowed to remove participants.' +
                    ' Contact your project admin for the same.' in
                    response.data
                )
                self.assertTrue(
                    self.reg_user2 in [
                        m.user for m in project.members
                    ]
                )

            # Check with admin member
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                self.assertTrue(self.reg_user1.is_admin_of_project(project))

                self.assertFalse(
                    self.reg_user2 not in [
                        m.user for m in project.members
                    ]
                )
                response = c.post(
                    '/project-%d/participant-%d/-remove' % (
                        project.id, self.reg_user2.id
                    ), headers=self.xhr_header,
                )

                # Checking json {"success": true}
                self.assertTrue(json.loads(response.data)['success'])
                self.assertEqual(response.status_code, 200)
                self.assertTrue(
                    self.reg_user2 not in [
                        m.user for m in project.members
                    ]
                )

                # Checks if remove participant by get request
                response = c.get(
                    '/project-%d/participant-%d/-remove' % (
                        project.id, self.reg_user2.id
                    )
                )

                self.assertEqual(response.status_code, 302)

                # Checks Flash Message
                response = c.get('/login')
                self.assertTrue(
                    'Could not remove participant! Try again.'
                    in response.data
                )

            # Check with project admin
            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                self.assertTrue(
                    self.project_admin_user.is_admin_of_project(project)
                )

                self.assertFalse(
                    self.reg_user3 not in [
                        m.user for m in project.members
                    ]
                )
                response = c.post(
                    '/project-%d/participant-%d/-remove' % (
                        project.id, self.reg_user3.id
                    ), headers=self.xhr_header,
                )

                # Checking json {"success": true}
                self.assertTrue(json.loads(response.data)['success'])
                self.assertEqual(response.status_code, 200)
                self.assertTrue(
                    self.reg_user3 not in [
                        m.user for m in project.members
                    ]
                )

                # Checks if remove participant by get request
                response = c.get(
                    '/project-%d/participant-%d/-remove' % (
                        project.id, self.reg_user2.id
                    )
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
        Checks that invitations can be removed by

        1. Project admin

        2. Admin member of the project
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user2.id,
                    }, {
                        'user': self.reg_user1.id,
                        'role': 'admin'
                    }])
                ]
            }])

            invitation1, = self.ProjectInvitation.create([{
                'email': 'email@reg_user3.com',
                'invitation_code': '123',
                'nereid_user': self.reg_user3.id,
                'project': project.id,
            }])

            invitation2, = self.ProjectInvitation.create([{
                'email': 'email@reg_user2.com',
                'invitation_code': '12345',
                'nereid_user': self.reg_user2.id,
                'project': project.id,
            }])

            # Check with non admin user
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user2.email, 'password')
                response = c.post(
                    '/invitation-%d/-remove' % invitation1.id
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
                    '/invitation-%d/-remove' % invitation1.id
                )
                self.assertEqual(response.status_code, 302)

            # Check with admin member
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')
                response = c.post(
                    '/invitation-%d/-remove' % invitation1.id
                )
                self.assertEqual(response.status_code, 302)
                response = c.get('/login')
                self.assertTrue(
                    u"Invitation to the user has been voided."
                    "The user can no longer join the project unless reinvited"
                    in response.data
                )

            # Check with project admin member
            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )
                response = c.post(
                    '/invitation-%d/-remove' % invitation2.id
                )
                self.assertEqual(response.status_code, 302)
                response = c.get('/login')
                self.assertTrue(
                    u"Invitation to the user has been voided."
                    "The user can no longer join the project unless reinvited"
                    in response.data
                )

    def test_0190_resend_invite(self):
        """
        Checks that only project admin or admin member of project can resend
        invites
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work.id,
                'type': 'project',
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id,
                        'role': 'admin',
                    }, {
                        'user': self.reg_user2.id,
                    }])
                ]
            }])

            invitation, = self.ProjectInvitation.create([{
                'email': 'email@reg_user2.com',
                'invitation_code': '123',
                'nereid_user': self.reg_user3.id,
                'project': project.id,
            }])

            # Check with admin member
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')
                response = c.post(
                    '/invitation-%d/-resend' % invitation.id,
                    headers=self.xhr_header,
                )

                # Checking json {"success": true}
                self.assertTrue(json.loads(response.data)['success'])
                self.assertEqual(response.status_code, 200)

            # Check with project admin
            with app.test_client() as c:

                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )
                response = c.post(
                    '/invitation-%d/-resend' % invitation.id,
                    headers=self.xhr_header,
                )

                # Checking json {"success": true}
                self.assertTrue(json.loads(response.data)['success'])
                self.assertEqual(response.status_code, 200)

            # Check with non admin member
            with app.test_client() as c:

                # User Login
                response = self.login(c, self.reg_user2.email, 'password')
                response = c.post(
                    '/invitation-%d/-resend' % invitation.id,
                    headers=self.xhr_header,
                )

                response = c.get('/login')
                self.assertTrue(
                    'Sorry! You are not allowed to resend invites. '
                    'Contact your project admin for the same.'
                    in response.data
                )

    def test_0190_constraints(self):
        """
        Checks unique constraint on project and nereid user
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults()

            # Create Project
            work, = self.Work.create([{
                'name': 'ABC',
                'company': self.company.id,
            }])

            task, = self.Project.create([{
                'work': work.id,
                'type': 'task',
                'parent': False,
                'state': 'opened',
            }])

            # Add participant to project
            self.TaskUsers.create([{
                'task': task.id,
                'user': self.reg_user2.id,
            }])
            self.assertRaises(
                Exception, self.TaskUsers.create,
                [{
                    'user': self.reg_user2.id,
                    'task': task.id,
                }]
            )

    def test_0200_stream_with_project(self):
        '''
        Tests that if user is part of project then he must be able to see all
        the activity streams of projects where he is participant
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app()

            work1, = self.Work.create([{
                'name': 'Test Project1',
                'company': self.company.id,
            }])
            work2, = self.Work.create([{
                'name': 'Test Project2',
                'company': self.company.id,
            }])

            project1, = self.Project.create([{
                'work': work1.id,
                'type': 'project',
                'parent': False,
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id
                    }])
                ]
            }])
            project2, = self.Project.create([{
                'work': work2.id,
                'type': 'project',
                'parent': False,
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user2.id
                    }])
                ]
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
                rv = self.login(c, self.reg_user1.email, 'password')
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
            self.create_defaults()
            app = self.get_app()

            work1, = self.Work.create([{
                'name': 'Test Project1',
                'company': self.company.id,
            }])
            work2, = self.Work.create([{
                'name': 'Test Project2',
                'company': self.company.id,
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
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id
                    }])
                ]
            }])
            project_model, = self.Model.search([
                ('model', '=', 'project.work')
            ])

            # Activities created by logged-in user
            self.Activity.create([{
                'verb': 'Add project 1',
                'actor': self.reg_user1.id,
                'object_': 'project.work,%s' % project1.id,
                'project': project1.id,
            }])

            self.Activity.create([{
                'verb': 'Add project 1 again',
                'actor': self.reg_user1.id,
                'object_': 'project.work,%s' % project2.id,
            }])

            # Create activity for different user
            self.Activity.create([{
                'verb': 'Add project 2',
                'actor': self.nereid_user_actor.id,
                'object_': 'project.work,%s' % project2.id,
            }])

            with app.test_client() as c:
                # User Login
                rv = self.login(c, self.reg_user1.email, 'password')
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

    def test_0210_check_gantt_data_access(self):
        """
        Check if only project manager and project admin can access
        gantt data.
        """
        # Check if unregistered users don't have access to gantt data
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app()

            with app.test_client() as c:

                with self.assertRaises(RuntimeError):
                    gantt_data = self.Project.get_gantt_data()

        # Check if Project Admin has access to gantt data
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app()

            with app.test_client() as c:

                # User Login
                rv = self.login(c, self.project_admin_user.email, 'password')
                self.assertEqual(rv.status_code, 302)

                gantt_data = self.Project.get_gantt_data()
                self.assert_(gantt_data)

        # Check if Project Manager has access to gantt data
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app()

            with app.test_client() as c:

                # User Login
                rv = self.login(c, self.project_manager_user.email, 'password')
                self.assertEqual(rv.status_code, 302)

                gantt_data = self.Project.get_gantt_data()
                self.assert_(gantt_data)

        # Check if users other than project admin and project manager
        # don't have access to gantt data
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app()

            with app.test_client() as c:

                # User Login
                rv = self.login(c, self.reg_user1.email, 'password')
                self.assertEqual(rv.status_code, 302)

                with self.assertRaises(Forbidden):
                    gantt_data = self.Project.get_gantt_data()

    def test_0200_check_all_participants_admins(self):
        '''
        Check all participants of the projects and tasks
        '''
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults_for_project()

            work1, = self.Work.create([{
                'name': 'Test Project1',
                'company': self.company.id,
            }])
            work2, = self.Work.create([{
                'name': 'Test Project2',
                'company': self.company.id,
            }])

            project, = self.Project.create([{
                'work': work1.id,
                'type': 'project',
                'parent': False,
                'state': 'opened',
                'members': [
                    ('create', [{
                        'user': self.reg_user1.id
                    }, {
                        'user': self.reg_user2.id
                    }, {
                        'user': self.reg_user3.id,
                        'role': 'admin'
                    }])
                ]
            }])
            task, = self.Project.create([{
                'work': work2.id,
                'type': 'task',
                'parent': project.id,
                'state': 'opened',
                'participants': [('set', [self.reg_user2.id])]
            }])

            # Project has 3 participants
            self.assertTrue(len(project.members), 3)

            # Task has 1 participants
            self.assertTrue(len(task.participants), 1)

            self.assertTrue(self.reg_user1 in project.all_participants)
            self.assertTrue(self.reg_user2 in project.all_participants)
            self.assertTrue(self.reg_user3 in project.all_participants)

            # All participants of task must be same as all participants of
            # project
            self.assertEqual(
                len(project.all_participants),
                len(task.all_participants),
            )
            self.assertTrue(self.reg_user1 in task.all_participants)
            self.assertTrue(self.reg_user2 in task.all_participants)
            self.assertTrue(self.reg_user3 in task.all_participants)

            self.assertTrue(self.reg_user1 not in project.admins)
            self.assertTrue(self.reg_user2 not in project.admins)
            self.assertTrue(self.reg_user3 in project.admins)


def suite():
    "Nereid test suite"
    test_suite = unittest.TestSuite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestProject)
    )
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
