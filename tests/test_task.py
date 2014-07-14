# -*- coding: utf-8 -*-
"""
    test_task

    TestTask

    :copyright: (c) 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest
import json
import smtplib

from trytond.config import CONFIG
CONFIG['smtp_from'] = 'test@openlabs.co.in'
CONFIG['data_path'] = '.'
from minimock import Mock

from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction
from test_base import TestBase

smtplib.SMTP = Mock('smtplib.SMTP')
smtplib.SMTP.mock_returns = Mock('smtp_connection')


class TestTask(TestBase):
    '''
    Test Task
    '''

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
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Create Task
                response = c.post(
                    '/project-%d/task/-new' % self.project1.id,
                    data={
                        'name': 'Test Task',
                        'description': 'task_desc',
                    }
                )
                self.assertEqual(response.status_code, 302)

                response = c.get('/login')
                self.assertTrue(
                    u'Task successfully added to project ABC' in
                    response.data
                )

                task, = self.Project.search([
                    ('type', '=', 'task'),
                    ('rec_name', '=', 'Test Task')
                ])

                self.assertEqual(task.state, 'opened')
                self.assertEqual(task.progress_state, 'Backlog')

    def test_0020_edit_task(self):
        """
        Test edit tasks added by logged in user
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Edit Task
                response = c.post(
                    '/task-%d/-edit' % self.task1.id,
                    data={
                        'name': 'ABC_task',
                        'comment': 'task_desc2',
                    },
                    headers=self.xhr_header,
                )
                self.assertEqual(response.status_code, 200)

                self.assertTrue(json.loads(response.data)['success'])
                self.assertEqual(self.task1.comment, 'task_desc2')

    def test_0030_watch_unwatch(self):
        """
        Test watching and unwatching of a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user2.email, 'password')

                # Unwatching task
                response = c.post(
                    '/task-%d/-unwatch' % self.task1.id,
                    data={},
                    headers=self.xhr_header,
                )
                self.assertEqual(response.status_code, 200)

                self.assertTrue(json.loads(response.data)['success'])
                self.assertFalse(
                    self.reg_user2 in self.task1.participants
                )

                # Watching task
                response = c.post(
                    '/task-%d/-watch' % self.task1.id,
                    data={},
                    headers=self.xhr_header,
                )
                self.assertEqual(response.status_code, 200)

                self.assertTrue(json.loads(response.data)['success'])
                self.assertTrue(
                    self.reg_user2 in self.task1.participants
                )

    def test_0040_update_task(self):
        """
        Test task update from user.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Add Comment without xhr
                response = c.post(
                    '/task-%d/-update' % self.task1.id,
                    data={
                        'comment': 'comment1',
                    }
                )
                self.assertEqual(response.status_code, 302)

                # Add Comment with XHR
                response = c.post(
                    '/task-%d/-update' % self.task1.id,
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
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Clear Assigned User
                response = c.post(
                    '/task-%d/-remove-assign' % self.task1.id,
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
            self.create_defaults_for_project()
            app = self.get_app()
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Assign User
                response = c.post(
                    '/task-%d/-assign' % self.task1.id,
                    data={
                        'user': self.reg_user2.id,
                    },
                    headers=self.xhr_header,
                )
                self.assertEqual(response.status_code, 200)

                self.assertTrue(json.loads(response.data)['success'])

                # Change Assigned User
                response = c.post(
                    '/task-%d/-assign' % self.task1.id,
                    data={
                        'user': self.reg_user1.id,
                    }
                )
                self.assertEqual(response.status_code, 302)

    def test_0070_state_change(self):
        """
        Test state update of a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Update with state change
                response = c.post(
                    '/task-%d/-update' % self.task1.id,
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
            self.create_defaults_for_project()
            app = self.get_app()
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # add_tag tag1
                response = c.post(
                    '/task-%d/tag-%d/-add' %
                    (self.task1.id, self.tag1.id), data={}
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
                    (self.task1.id, self.tag2.id), data={}
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
                    (self.task1.id, self.tag1.id), data={}
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
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Render_task_list for project
                response = c.get(
                    '/project-%d/task-list' % self.project1.id,
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
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Render_task_list for project with query 'test'
                response = c.get(
                    '/project-%d/task-list?q=test' %
                    self.project1.id, headers=self.xhr_header,
                )

                # Checking list count
                self.assertEqual(
                    len(json.loads(response.data)['items']), 0
                )

                # Render_task_list for project with query 'task3'
                response = c.get(
                    '/project-%d/task-list?q=task3' %
                    self.project1.id, headers=self.xhr_header,
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
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Render_task_list for project with tag 'tag1'
                response = c.get(
                    '/project-%d/task-list?tag=%d' %
                    (self.project1.id, self.tag1.id),
                    headers=self.xhr_header,
                )

                # Checking list count
                self.assertEqual(
                    len(json.loads(response.data)['items']), 0
                )

                # Render_task_list for project with tag 'tag2'
                response = c.get(
                    '/project-%d/task-list?tag=%d' %
                    (self.project1.id, self.tag2.id),
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
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                with Transaction().set_context({"company": self.company.id}):
                    # Mark time
                    response = c.post(
                        '/task-%d/-mark-time' % self.task1.id,
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
                response = self.login(c, self.reg_user3.email, 'password')

                # Mark time when user is not employee
                response = c.post(
                    '/task-%d/-mark-time' % self.task1.id,
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
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Change estimated hours
                response = c.post(
                    '/task-%d/change-estimated-hours' % self.task1.id,
                    data={
                        'new_estimated_hours': '15',
                    }
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(self.task1.effort, 15)

    def test_0140_check_my_tasks(self):
        """
        Check my tasks.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()
            task = self.task1

            self.Project.write([task], {
                'assigned_to': self.reg_user1.id,
            })

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Check my tasks
                response = c.get(
                    '/my-tasks', headers=self.xhr_header
                )
                self.assertEqual(
                    len(json.loads(response.data)['items']), 1
                )

                # Check my tasks with tag1
                response = c.get(
                    '/my-tasks?tag=%d' % self.tag1.id,
                    headers=self.xhr_header
                )
                self.assertEqual(
                    len(json.loads(response.data)['items']), 0
                )

                # Check my tasks with tag2
                response = c.get(
                    '/my-tasks?tag=%d' % self.tag2.id,
                    headers=self.xhr_header
                )
                self.assertEqual(
                    len(json.loads(response.data)['items']), 1
                )

    def test_0150_render_tasks_by_employee(self):
        """
        Render tasks by employee.
        """
        # Project admin user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                # Render_tasks_by_employee
                response = c.get('/tasks-by-employee')
                self.assertEqual(response.status_code, 200)

        # Project manager user
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(
                    c, self.project_manager_user.email, 'password'
                )

                # Render_tasks_by_employee
                response = c.get('/tasks-by-employee')
                self.assertEqual(response.status_code, 200)

        # Neither project admin nor manager
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Render_tasks_by_employee
                response = c.get('/tasks-by-employee')
                self.assertEqual(response.status_code, 403)

    def test_0160_render_task(self):
        """
        Render a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Render_task
                response = c.get(
                    '/project-%d/task-%d' % (
                        self.task1.parent.id, self.task1.id
                    )
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, str(self.task1.id))

    def test_0170_update_comment(self):
        """
        Update a previous comment on a task.
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            comment, = self.History.create([{
                'project': self.task1.id,
                'updated_by': self.reg_user1.id,
                'comment': 'comment1',
            }])

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Update_comment
                response = c.post(
                    '/task-%d/comment-%d/-update' %
                    (self.task1.id, comment.id), data={'comment': 'comment2'},
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
            self.create_defaults_for_project()
            app = self.get_app()

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Change_constraint_dates
                response = c.post(
                    '/task-%d/change_constraint_dates' % self.task1.id,
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
        Tests that task can be deleted only by

        1. Project Admin
        2. Admin member of the project
        """
        ProjectMember = POOL.get('project.work.member')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            # Case1: When user is not admin member in the project
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user2.email, 'password')

                self.assertFalse(
                    self.reg_user2.is_admin_of_project(self.task1.parent)
                )

                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    3
                )
                # Delete_task
                response = c.post(
                    '/task-%d/-delete' % self.task1.id,
                    headers=self.xhr_header
                )
                self.assertEqual(response.status_code, 302)

                # Task is not deleted
                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    3
                )

            # Case2: When user is admin member in the project
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user2.email, 'password')

                self.assertFalse(
                    self.reg_user2.is_admin_of_project(self.task1.parent)
                )

                project_user, = ProjectMember.search([
                    ('user', '=', self.reg_user2.id),
                    ('project', '=', self.task1.parent)
                ])
                project_user.role = 'admin'
                project_user.save()

                self.assertTrue(
                    self.reg_user2.is_admin_of_project(self.task1.parent)
                )

                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    3
                )
                # Delete_task
                response = c.post(
                    '/task-%d/-delete' % self.task1.id,
                    headers=self.xhr_header
                )
                self.assertEqual(response.status_code, 200)

                self.assertTrue(json.loads(response.data)['success'])

                # Total tasks before deletion are 3 after deletion 2
                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    2
                )

            # Case3: When user is project admin
            with app.test_client() as c:
                # User Login
                response = self.login(
                    c, self.project_admin_user.email, 'password'
                )

                self.assertTrue(
                    self.reg_user2.is_admin_of_project(self.task2.parent)
                )

                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    2
                )
                # Delete_task
                response = c.post(
                    '/task-%d/-delete' % self.task2.id,
                    headers=self.xhr_header
                )
                self.assertEqual(response.status_code, 200)

                self.assertTrue(json.loads(response.data)['success'])

                # Total tasks before deletion are 2, after deletion 1
                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    1
                )

    def test_0200_create_task_with_multiple_tags(self):
        """
        Tests that task can be created with mulitple tags only if user is

        1. Project Admin or
        2. Admin member of the project
        """
        ProjectMember = POOL.get('project.work.member')

        # As non admin member
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app(DEBUG=True)

            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    3
                )

                # Create Task
                response = c.post(
                    '/project-%d/task/-new' % self.project1.id,
                    data={
                        'name': 'Task with multiple tags',
                        'description': 'Multi selection tags field',
                        'tags': [
                            self.tag1.id,
                            self.tag2.id,
                            self.tag3.id,
                        ],
                    }
                )
                self.assertEqual(response.status_code, 302)
                # One task created
                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    4
                )
                self.assertTrue(
                    self.Project.search([
                        ('rec_name', '=', 'Task with multiple tags')
                    ])
                )

                task, = self.Project.search([
                    ('rec_name', '=', 'Task with multiple tags'),
                ])

                # Tags are not added in above created task since user
                # is not admin member
                self.assertEqual(len(task.tags), 0)

            # As project admin
            with app.test_client() as c:

                member, = ProjectMember.search([
                    ('user.email', '=', 'email@reg_user1.com'),
                    ('project', '=', self.project1.id),
                ])
                member.role = 'admin'
                member.save()

                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    4
                )

                # Create Task
                response = c.post(
                    '/project-%d/task/-new' % self.project1.id,
                    data={
                        'name': 'Task 2 with multiple tags',
                        'description': 'Multi selection tags field',
                        'tags': [
                            self.tag1.id,
                            self.tag2.id,
                            self.tag3.id,
                        ],
                    }
                )
                self.assertEqual(response.status_code, 302)
                # One task created
                self.assertEqual(
                    len(self.Project.search([('type', '=', 'task')])),
                    5
                )
                self.assertTrue(
                    self.Project.search([
                        ('rec_name', '=', 'Task 2 with multiple tags')
                    ])
                )

                task, = self.Project.search([
                    ('rec_name', '=', 'Task 2 with multiple tags'),
                ])

                # Tags are addedd successfully
                self.assertEqual(len(task.tags), 3)

    def test_0220_unique_users_per_project(self):
        """
        Refer sentry issue:
        http://sentry.openlabs.co.in/default/my-openlabs-production/group/2271/
        """
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.create_defaults_for_project()
            app = self.get_app()

            # Nereid User-1 creates a task and assign it to himself
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Login Success
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, 'http://localhost/')

                response = c.post(
                    '/project-%d/task/-new' % self.project1.id,
                    data={
                        'name': 'Test Task 1',
                        'description': 'task_desc',
                        'assign_to': self.reg_user1.id,
                    }
                )
                self.assertEqual(response.status_code, 302)

                response = c.get('/login')
                self.assertTrue(
                    u'Task successfully added to project ABC' in
                    response.data
                )

            # Nereid User-1 creates a task and assign it to other
            # participant of the project
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Login Success
                self.assertEqual(response.status_code, 302)
                response = c.post(
                    '/project-%d/task/-new' % self.project1.id,
                    data={
                        'name': 'Test Task 2',
                        'description': 'task_desc',
                        'assign_to': self.reg_user2.id,
                    }
                )
                self.assertEqual(response.status_code, 302)

                response = c.get('/login')
                self.assertTrue(
                    u'Task successfully added to project ABC' in
                    response.data
                )

            # Nereid User-1 creates a task and assign it to non
            # participant user
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user1.email, 'password')

                # Login Success
                self.assertEqual(response.status_code, 302)
                response = c.post(
                    '/project-%d/task/-new' % self.project1.id,
                    data={
                        'name': 'Test Task 3',
                        'description': 'task_desc',
                        'assign_to': self.reg_user3.id,
                    }
                )
                self.assertEqual(response.status_code, 404)

            task, = self.Project.search([
                ('type', '=', 'task'), ('work.name', '=', 'Test Task 1')
            ])

            # Nereid User-2 updates the task and assigned to himself
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user2.email, 'password')

                response = c.post(
                    '/task-%d/-update' % task.id,
                    data={
                        'comment': 'comment1',
                        'assigned_to': self.reg_user2.id,
                        'progress_state': 'In Progress',
                    },
                    headers=self.xhr_header,
                )
                self.assertEqual(response.status_code, 200)

            # Nereid User-2 updates the task and assigned to other
            # participant of the project
            with app.test_client() as c:
                # User Login
                response = self.login(c, self.reg_user2.email, 'password')

                # Login Success
                self.assertEqual(response.status_code, 302)

                response = c.post(
                    '/task-%d/-update' % task.id,
                    data={
                        'comment': 'comment1',
                        'assigned_to': self.reg_user1.id,
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
