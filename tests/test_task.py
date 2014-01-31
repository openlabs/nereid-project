# -*- coding: utf-8 -*-
"""
    test_task

    TestTask

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest
import json
import smtplib
import pytz

from trytond.config import CONFIG
CONFIG['smtp_from'] = 'test@openlabs.co.in'
CONFIG['data_path'] = '.'
from minimock import Mock
from datetime import datetime

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction
#from trytond.error import UserError
from nereid.testing import NereidTestCase

smtplib.SMTP = Mock('smtplib.SMTP')
smtplib.SMTP.mock_returns = Mock('smtp_connection')


class TestTask(NereidTestCase):
    '''
    Test Task
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
        self.Project = POOL.get('project.work')
        self.Timesheet = POOL.get('timesheet.line')
        self.Tag = POOL.get('project.work.tag')
        self.History = POOL.get('project.work.history')
        self.Permission = POOL.get('nereid.permission')
        self.ProjectWorkCommit = POOL.get('project.work.commit')
        self.Activity = POOL.get('nereid.activity')
        self.Locale = POOL.get('nereid.website.locale')
        self.xhr_header = [
            ('X-Requested-With', 'XMLHttpRequest'),
        ]

    def create_defaults(self):
        """
        Setup the defaults for all tests.
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
        party0, party1, party2, = self.Party.create([{
            'name': 'Non registered user',
        }, {
            'name': 'Registered User1',
        }, {
            'name': 'Registered User2',
        }])

        # Create guest user
        guest_user, = self.NereidUser.create([{
            'party': party0.id,
            'display_name': 'Guest User',
            'email': 'guest@openlabs.co.in',
            'password': 'password',
            'company': company.id,
        }])

        employee1, = self.Employee.create([{
            'company': company.id,
            'party': party1.id,
        }])
        registered_user1, = self.NereidUser.create([{
            'party': party1.id,
            'display_name': 'Registered User',
            'email': 'email@example.com',
            'password': 'password',
            'company': company.id,
            'employee': employee1.id,
        }])
        registered_user2, = self.NereidUser.create([{
            'party': party2.id,
            'display_name': 'Registered User',
            'email': 'example@example.com',
            'password': 'password',
            'company': company.id,
        }])
        self.Company.write([company], {
            'project_admins': [('add', [registered_user1.id])],
            'employees': [('add', [employee1.id])],
        })
        menu_list = self.Action.search([('usage', '=', 'menu')])
        user1, = self.User.create([{
            'name': 'res_user1',
            'login': 'res_user1',
            'password': '1234',
            'menu': menu_list[0].id,
            'main_company': company.id,
            'company': company.id,
        }])
        user2, = self.User.create([{
            'name': 'res_user2',
            'login': 'res_user2',
            'password': '5678',
            'menu': menu_list[0].id,
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

        # Create project
        work1, = self.Work.create([{
            'name': 'ABC',
            'company': company.id,
        }])
        project1, = self.Project.create([{
            'work': work1.id,
            'type': 'project',
            'state': 'opened',
        }])

        # Create Tags
        tag1, = self.Tag.create([{
            'name': 'tag1',
            'color': 'color1',
            'project': project1.id
        }])
        tag2, = self.Tag.create([{
            'name': 'tag2',
            'color': 'color2',
            'project': project1.id
        }])
        tag3, = self.Tag.create([{
            'name': 'tag3',
            'color': 'color3',
            'project': project1.id
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

        self.templates = {
            'login.jinja': '{{ get_flashed_messages()|safe }}',
            'project/comment.jinja': '',
            'project/emails/text_content.jinja': '',
            'project/emails/html_content.jinja': '',
            'project/task.jinja': '{{ task.id }}',
            'project/comment.jinja': '',
            'project/tasks-by-employee.jinja': '',
            'project/project-task-list.jinja': '{{ tasks|length }}',
        }

        return {
            'company': company,
            'employee1': employee1,
            'party1': party1,
            'party2': party2,
            'nereid_project_website': nereid_project_website,
            'registered_user1': registered_user1,
            'registered_user2': registered_user2,
            'guest_user': guest_user,
            'user1': user1,
            'user2': user2,
            'work1': work1,
            'project1': project1,
            'tag1': tag1,
            'tag2': tag2,
            'tag3': tag3,
        }

    def create_task_dafaults(self):
        '''
        Create Default for from create_defaults() Task.
        '''
        data = self.create_defaults()
        data['work2'], = self.Work.create([{
            'name': 'ABC_task',
            'company': data['company'].id,
        }])
        data['task1'], = self.Project.create([{
            'work': data['work2'].id,
            'comment': 'task_desc',
            'parent': data['project1'].id,
        }])
        data['work3'], = self.Work.create([{
            'name': 'ABC_task2',
            'company': data['company'].id,
        }])
        data['task2'], = self.Project.create([{
            'work': data['work3'].id,
            'comment': 'task_desc',
            'parent': data['project1'].id,
        }])
        data['work4'], = self.Work.create([{
            'name': 'ABC_task3',
            'company': data['company'].id,
        }])
        data['task3'], = self.Project.create([{
            'work': data['work4'].id,
            'comment': 'task_desc',
            'parent': data['project1'].id,
        }])

        self.Project.write(
            [data['task1'].parent],
            {
                'participants': [
                    ('add', [
                        data['registered_user2'].id,
                        data['registered_user1'].id
                    ])
                ]
            }
        )

        # Add tag2 to task
        self.Project.write(
            [data['task1'], data['task2']],
            {'tags': [('add', [data['tag2'].id])]}
        )

        return data

    def get_template_source(self, name):
        """
        Return templates.
        """
        return self.templates.get(name)

    def test_0010_create_task(self):
        """
        Test create task by logged in user
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app()

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }

            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Create Task
                    response = c.post(
                        '/project-%d/task/-new' % data['project1'].id,
                        data={
                            'name': 'ABC_task',
                            'description': 'task_desc',
                        }
                    )
                    self.assertEqual(response.status_code, 302)

                    response = c.get('/login')
                    self.assertTrue(
                        u'Task successfully added to project ABC' in
                        response.data
                    )

    def test_0020_edit_task(self):
        """
        Test edit tasks added by logged in user
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Edit Task
                    response = c.post(
                        '/task-%d/-edit' % task.id,
                        data={
                            'name': 'ABC_task',
                            'comment': 'task_desc2',
                        },
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)

                    self.assertTrue(json.loads(response.data)['success'])
                    self.assertEqual(data['task1'].comment, 'task_desc2')

    def test_0030_watch_unwatch(self):
        """
        Test watching and unwatching of a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Unwatching task
                    response = c.post(
                        '/task-%d/-unwatch' % task.id,
                        data={},
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)

                    self.assertTrue(json.loads(response.data)['success'])
                    self.assertFalse(
                        data['registered_user1'] in task.participants
                    )

                    # Watching task
                    response = c.post(
                        '/task-%d/-watch' % data['task1'].id,
                        data={},
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)

                    self.assertTrue(json.loads(response.data)['success'])
                    self.assertTrue(
                        data['registered_user1'] in task.participants
                    )

    def test_0040_update_task(self):
        """
        Test task update from user.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Add Comment without xhr
                    response = c.post(
                        '/task-%d/-update' % task.id,
                        data={
                            'comment': 'comment1',
                        }
                    )
                    self.assertEqual(response.status_code, 302)

                    # Add Comment with XHR
                    response = c.post(
                        '/task-%d/-update' % task.id,
                        data={
                            'comment': 'comment2',
                        },
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)

                    self.assertTrue(json.loads(response.data)['success'])

    def test_0050_clear_assigned_user(self):
        """
        Test clear assigned user from a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Clear Assigned User
                    response = c.post(
                        '/task-%d/-remove-assign' % task.id,
                        data={},
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)

                    self.assertTrue(json.loads(response.data)['success'])

    def test_0060_assign_user(self):
        """
        Test assigning task to a User.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Assign User
                    response = c.post(
                        '/task-%d/-assign' % task.id,
                        data={
                            'user': data['registered_user2'].id,
                        },
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)

                    self.assertTrue(json.loads(response.data)['success'])

                    # Change Assigned User
                    response = c.post(
                        '/task-%d/-assign' % task.id,
                        data={
                            'user': data['registered_user1'].id,
                        }
                    )
                    self.assertEqual(response.status_code, 302)

    def test_0070_state_change(self):
        """
        Test state update of a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                # Update with state change
                response = c.post(
                    '/task-%d/-update' % task.id,
                    data={
                        'progress_state': 'Planning',
                        'state': 'opened',
                        'comment': 'comment1',
                    }
                )
                self.assertEqual(response.status_code, 302)

    def test_0080_add_remove_tag(self):
        """
        Test to add and remove tag from task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # add_tag tag1
                    response = c.post(
                        '/task-%d/tag-%d/-add' %
                        (task.id, data['tag1'].id), data={}
                    )
                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Tag added to task ABC_task' in response.data
                    )

                    # Add_tag tag2
                    response = c.post(
                        '/task-%d/tag-%d/-add' %
                        (data['task1'].id, data['tag2'].id), data={}
                    )

                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Tag added to task ABC_task' in response.data
                    )

                    # Remove_tag tag1
                    response = c.post(
                        '/task-%d/tag-%d/-remove' %
                        (data['task1'].id, data['tag1'].id), data={}
                    )

                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Tag removed from task ABC_task' in response.data
                    )

    def test_0090_render_task_list(self):
        """
        Test render task list for a project.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Render_task_list for project
                    response = c.get(
                        '/project-%d/task-list' % data['project1'].id,
                        headers=self.xhr_header,
                    )

                    # Checking list count
                    self.assertEqual(
                        len(json.loads(response.data)['items']), 3
                    )

    def test_0100_render_task_search_with_query(self):
        """
        Tests if task can be searched by providing some query.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Render_task_list for project with query 'test'
                    response = c.get(
                        '/project-%d/task-list?q=test' %
                        data['project1'].id, headers=self.xhr_header,
                    )

                    # Checking list count
                    self.assertEqual(
                        len(json.loads(response.data)['items']), 0
                    )

                    # Render_task_list for project with query 'task3'
                    response = c.get(
                        '/project-%d/task-list?q=task3' %
                        data['project1'].id, headers=self.xhr_header,
                    )

                    # Checking list count
                    self.assertEqual(
                        len(json.loads(response.data)['items']), 1
                    )

    def test_0110_render_task_search_by_tag(self):
        """
        Test render task list for a project with tag.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Render_task_list for project with tag 'tag1'
                    response = c.get(
                        '/project-%d/task-list?tag=%d' %
                        (data['project1'].id, data['tag1'].id),
                        headers=self.xhr_header,
                    )

                    # Checking list count
                    self.assertEqual(
                        len(json.loads(response.data)['items']), 0
                    )

                    # Render_task_list for project with tag 'tag2'
                    response = c.get(
                        '/project-%d/task-list?tag=%d' %
                        (data['project1'].id, data['tag2'].id),
                        headers=self.xhr_header,
                    )

                    # Checking list count
                    self.assertEqual(
                        len(json.loads(response.data)['items']), 2
                    )

    def test_0120_mark_time(self):
        """
        Test marking time.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            login_data2 = {
                'email': 'example@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')
                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Mark time
                    response = c.post(
                        '/task-%d/-mark-time' % task.id,
                        data={
                            'hours': '8',
                        }
                    )

                    self.assertEqual(response.status_code, 302)

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Time has been marked on task ABC_task' in
                        response.data
                    )

                    # Logout
                    response = c.get('/logout')

                    # Login with other user
                    response = c.post('/login', data=login_data2)

                    # Login Success
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(
                        response.location, 'http://localhost/'
                    )

                    # Mark time when user is not employee
                    response = c.post(
                        '/task-%d/-mark-time' % task.id,
                        data={
                            'hours': '8',
                        }
                    )

                    self.assertEqual(response.status_code, 302)
                    response = c.get('/logout')

                    # Check Flash Message
                    response = c.get('/login')
                    self.assertTrue(
                        u'Only employees can mark time on tasks!' in
                        response.data
                    )

    def test_0130_change_estimated_hours(self):
        """
        Test changing estimated hours of a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Change estimated hours
                    response = c.post(
                        '/task-%d/change-estimated-hours' % task.id,
                        data={
                            'new_estimated_hours': '15',
                        }
                    )
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(task.effort, 15)

    def test_0140_check_my_tasks(self):
        """
        Check my tasks.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            self.Project.write([task], {
                'assigned_to': data['registered_user1'].id,
            })

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Check my tasks
                    response = c.get(
                        '/my-tasks', headers=self.xhr_header
                    )
                    self.assertEqual(
                        len(json.loads(response.data)['items']), 1
                    )

                    # Check my tasks with tag1
                    response = c.get(
                        '/my-tasks?tag=%d' % data['tag1'].id,
                        headers=self.xhr_header
                    )
                    self.assertEqual(
                        len(json.loads(response.data)['items']), 0
                    )

                    # Check my tasks with tag2
                    response = c.get(
                        '/my-tasks?tag=%d' % data['tag2'].id,
                        headers=self.xhr_header
                    )
                    self.assertEqual(
                        len(json.loads(response.data)['items']), 1
                    )

    def test_0150_render_tasks_by_employee(self):
        """
        Render tasks by employee.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Render_tasks_by_employee
                    response = c.get('/tasks-by-employee')
                    self.assertEqual(response.status_code, 200)

    def test_0160_render_task(self):
        """
        Render a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Render_task
                    response = c.get(
                        '/project-%d/task-%d' % (task.parent.id, task.id)
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, str(task.id))

    def test_0170_update_comment(self):
        """
        Update a previous comment on a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            comment, = self.History.create([{
                'project': task.id,
                'updated_by': data['registered_user1'].id,
                'comment': 'comment1',
            }])
            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Update_comment
                    response = c.post(
                        '/task-%d/comment-%d/-update' %
                        (task.id, comment.id), data={'comment': 'comment2'},
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)

                    self.assertTrue(json.loads(response.data)['success'])
                    self.assertEqual(comment.comment, 'comment2')

    def test_0180_change_constraint_dates(self):
        """
        Change estimated hours of a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # Change_constraint_dates
                    response = c.post(
                        '/task-%d/change_constraint_dates' % task.id,
                        data={
                            'constraint_start_time': '06/24/2013',
                            'constraint_finish_time': '06/30/2013',
                        },
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)

                    # Checking json success
                    self.assertTrue(json.loads(response.data)['success'])

    def test_0190_delete_task(self):
        """
        Delete a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    self.assertEqual(
                        len(self.Project.search([('type', '=', 'task')])),
                        3
                    )
                    # Delete_task
                    response = c.post(
                        '/task-%d/-delete' % task.id,
                        headers=self.xhr_header
                    )
                    self.assertEqual(response.status_code, 200)

                    self.assertTrue(json.loads(response.data)['success'])

                    # Total tasks before deletion are 3 after deletion 2
                    self.assertEqual(
                        len(self.Project.search([('type', '=', 'task')])),
                        2
                    )

    def test_0200_create_task_with_multiple_tags(self):
        """
        Adding more than one tag to task which already exist in a project
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app(DEBUG=True)

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            with app.test_client() as c:
                response = c.post('/login', data=login_data)
                self.assertEqual(response.status_code, 302)

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    # No task created
                    self.assertEqual(
                        len(self.Project.search([('type', '=', 'task')])),
                        0
                    )

                    # Create Task
                    response = c.post(
                        '/project-%d/task/-new' % data['project1'].id,
                        data={
                            'name': 'Task with multiple tags',
                            'description': 'Multi selection tags field',
                            'tags': [
                                data['tag1'].id,
                                data['tag2'].id,
                                data['tag3'].id,
                            ],
                        }
                    )
                    self.assertEqual(response.status_code, 302)
                    # One task created
                    self.assertEqual(
                        len(self.Project.search([('type', '=', 'task')])),
                        1
                    )
                    self.assertTrue(
                        self.Project.search([
                            ('rec_name', '=', 'Task with multiple tags')
                        ])
                    )

                    task, = self.Project.search([
                        ('rec_name', '=', 'Task with multiple tags'),
                    ])

                    # Tags added in above created task
                    self.assertEqual(len(task.tags), 3)

                    response = c.get('/login')
                    self.assertTrue(
                        u'Task successfully added to project ABC' in
                        response.data
                    )

    def test_0210_github_commit_activity_stream(self):
        """
        Checks activity stream generation for commit message and github hook
        handler
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_task_dafaults()
            app = self.get_app()
            task = data['task1']

            login_data = {
                'email': 'email@example.com',
                'password': 'password',
            }
            utc = pytz.UTC

            payload = {
                'commits': [{
                    'author': {'email': 'email@example.com'},
                    'message': 'Add commit #%d' % task.id,
                    'timestamp': str(utc.localize(datetime.utcnow())),
                    'url': 'repo/url/1',
                    'id': '54321',
                }],
                'repository': {
                    'name': 'ABC Repository',
                    'url': 'repo/url',
                }
            }

            with app.test_client() as c:
                response = c.post('/login', data=login_data)

                # Login Success
                self.assertEqual(response.status_code, 302)

                with Transaction().set_context(
                    {'company': data['company'].id}
                ):
                    self.assertEqual(
                        len(data['registered_user1'].activities), 0
                    )

                    # Check github handler
                    response = c.post(
                        '/-project/-github-hook',
                        data={
                            'payload': json.dumps(payload)
                        }
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.data, 'OK')

                    # Activity stream is created for commit user
                    self.assertEqual(
                        len(data['registered_user1'].activities), 1
                    )

                    commit, = self.ProjectWorkCommit.search([
                        ('commit_id', '=', '54321')
                    ])

                    activities = self.Activity.search([
                        ('object_', '=', 'project.work.commit, %d' % commit.id)
                    ]),

                    self.assertEqual(len(activities), 1)

    def test_0220_unique_users_per_project(self):
        """
        Refer sentry issue:
        http://sentry.openlabs.co.in/default/my-openlabs-production/group/2271/
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            data = self.create_defaults()
            app = self.get_app()

            # Add participants to project1
            self.Project.write([data['project1']], {
                'participants': [
                    ('add', [
                        data['registered_user2'].id,
                        data['registered_user1'].id
                    ])
                ]
            })

            login_data_user1 = {
                'email': 'email@example.com',
                'password': 'password',
            }

            # Nereid User-1 creates a task and assign it to himself
            with app.test_client() as c:
                response = c.post('/login', data=login_data_user1)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context({'company': data['company'].id}):
                    response = c.post(
                        '/project-%d/task/-new' % data['project1'].id,
                        data={
                            'name': 'ABC_task',
                            'description': 'task_desc',
                            'assign_to': data['registered_user1'].id,
                        }
                    )
                    self.assertEqual(response.status_code, 302)

                    response = c.get('/login')
                    self.assertTrue(
                        u'Task successfully added to project ABC' in
                        response.data
                    )

            task, = self.Project.search([('type', '=', 'task')])

            login_data_user2 = {
                'email': 'example@example.com',
                'password': 'password',
            }

            # Nereid User-2 updates the task and assigned to himself
            with app.test_client() as c:
                response = c.post('/login', data=login_data_user2)

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                with Transaction().set_context({'company': data['company'].id}):
                    response = c.post(
                        '/task-%d/-update' % task.id,
                        data={
                            'comment': 'comment1',
                            'assigned_to': data['registered_user2'].id,
                            'progress_state': 'In Progress',
                        },
                        headers=self.xhr_header,
                    )
                    self.assertEqual(response.status_code, 200)


def suite():
    "Nereid test suite"
    test_suite = unittest.TestSuite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestTask)
    )
    return test_suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
# pylint: enable-msg=C0103
