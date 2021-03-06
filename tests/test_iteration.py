# -*- coding: utf-8 -*-
"""
    test_iteration

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: see LICENSE for more details.
"""
import json
import datetime
import unittest

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction
from test_base import TestBase


class TestIteration(TestBase):
    '''
    Test Iteration.
    '''

    def test_0010_test_iteration_record_creation(self):
        """
        Test the project iteration
        """
        Iteration = POOL.get('project.iteration')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()

            work1, = self.Work.create([{
                'name': 'ABC Project',
                'company': self.company.id,
            }])
            project, = self.Project.create([{
                'work': work1.id,
                'type': 'project',
                'state': 'opened',
                'sequence': 1,
            }])
            self.assert_(project)

            work2, = self.Work.create([{
                'name': 'User Story',
                'company': self.company.id,
            }])

            task1, = self.Project.create([{
                'work': work2.id,
                'type': 'task',
                'parent': project.id,
                'state': 'opened',
            }])
            self.assert_(task1)

            work3, = self.Work.create([{
                'name': 'User Task',
                'company': self.company.id,
            }])

            task2, = self.Project.create([{
                'work': work3.id,
                'type': 'task',
                'parent': project.id,
                'state': 'opened',
            }])
            self.assert_(task2)
            with Transaction().set_context(company=self.company.id):
                iteration, = Iteration.create([{
                    'name': 'Iteration1',
                    'start_date': datetime.date(2011, 2, 3),
                    'end_date': datetime.date(2011, 2, 5),
                    'tasks': [('add', [task1.id, task2.id])],
                }])
            self.assert_(iteration)

            self.assertEqual(
                len(iteration.tasks), 2
            )

    def test_0020_test_iteration_creation(self):
        """
        Test creation of iteration
        """
        Iteration = POOL.get('project.iteration')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)
            with Transaction().set_context(company=self.company.id):
                work1, = self.Work.create([{
                    'name': 'ABC Project',
                    'company': self.company.id,
                }])
                project, = self.Project.create([{
                    'work': work1.id,
                    'type': 'project',
                    'state': 'opened',
                    'sequence': 1,
                }])
                self.assert_(project)

                work2, = self.Work.create([{
                    'name': 'User Story',
                    'company': self.company.id,
                }])

                task1, = self.Project.create([{
                    'work': work2.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task1)

                work3, = self.Work.create([{
                    'name': 'User Task',
                    'company': self.company.id,
                }])

                task2, = self.Project.create([{
                    'work': work3.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                with app.test_client() as c:
                    rv = self.login(
                        c, self.scrum_master_user.email, 'password'
                    )
                    self.assertEqual(rv.status_code, 302)
                    rv = c.post('/iterations/', data={
                        'name': 'Iteration1',
                        'start_date': datetime.date(2011, 2, 3).isoformat(),
                        'end_date': datetime.date(2011, 2, 5).isoformat(),
                    })
                    self.assertEqual(rv.status_code, 200)
                    rv_json = json.loads(rv.data)
                    self.assertTrue(rv_json.get('url'))
                    self.assertEqual(len(Iteration.search([])), 1)

                    # Get iterations
                    rv = c.get('/iterations/')
                    rv_json = json.loads(rv.data)
                    self.assertEqual(rv_json['count'], 1)

    def test_0030_test_render_iteration(self):
        """
        Test render iteration
        """
        Iteration = POOL.get('project.iteration')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)
            with Transaction().set_context(company=self.company.id):
                work1, = self.Work.create([{
                    'name': 'ABC Project',
                    'company': self.company.id,
                }])
                project, = self.Project.create([{
                    'work': work1.id,
                    'type': 'project',
                    'state': 'opened',
                    'sequence': 1,
                }])
                self.assert_(project)

                work2, = self.Work.create([{
                    'name': 'User Story',
                    'company': self.company.id,
                }])

                task1, = self.Project.create([{
                    'work': work2.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task1)

                work3, = self.Work.create([{
                    'name': 'User Task',
                    'company': self.company.id,
                }])

                task2, = self.Project.create([{
                    'work': work3.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task2)
                iteration, = Iteration.create([{
                    'name': 'Iteration1',
                    'start_date': datetime.date(2011, 2, 3),
                    'end_date': datetime.date(2011, 2, 5),
                    'tasks': [('add', [task1.id, task2.id])],
                }])
                self.assert_(iteration)
                with app.test_client() as c:
                    rv = self.login(
                        c, self.scrum_master_user.email, 'password'
                    )
                    self.assertEqual(rv.status_code, 302)
                    rv = c.get('/iterations/%s' % iteration.id)
                    self.assertEqual(rv.status_code, 200)
                    rv_json = json.loads(rv.data)
                    self.assertEqual(len(rv_json['tasks']), 2)

    def test_0040_test_add_task_to_iteration(self):
        """
        Test Adding task to iteration
        """
        Iteration = POOL.get('project.iteration')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)
            with Transaction().set_context(company=self.company.id):
                work1, = self.Work.create([{
                    'name': 'ABC Project',
                    'company': self.company.id,
                }])
                project, = self.Project.create([{
                    'work': work1.id,
                    'type': 'project',
                    'state': 'opened',
                    'sequence': 1,
                }])
                self.assert_(project)

                work2, = self.Work.create([{
                    'name': 'User Story',
                    'company': self.company.id,
                }])

                task1, = self.Project.create([{
                    'work': work2.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task1)

                work3, = self.Work.create([{
                    'name': 'User Task',
                    'company': self.company.id,
                }])

                task2, = self.Project.create([{
                    'work': work3.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task2)
                iteration, = Iteration.create([{
                    'name': 'Iteration1',
                    'start_date': datetime.date(2011, 2, 3),
                    'end_date': datetime.date(2011, 2, 5),
                    'tasks': [('add', [task1.id])],
                }])
                self.assert_(iteration)
                self.assertTrue(task1 in iteration.tasks)
                self.assertTrue(task2 not in iteration.tasks)
                with app.test_client() as c:
                    rv = self.login(
                        c, self.scrum_master_user.email, 'password'
                    )
                    # Add task to iteration
                    self.assertEqual(rv.status_code, 302)
                    rv = c.post(
                        '/iterations/%s' % iteration.id, data={
                            'action': 'add',
                            'task_id': task2.id
                        }
                    )
                    self.assertEqual(rv.status_code, 200)
                    iteration = Iteration(iteration.id)
                    self.assertTrue(task1 in iteration.tasks)
                    self.assertTrue(task2 in iteration.tasks)

                    # remove task from iteration
                    rv = c.post(
                        '/iterations/%s' % iteration.id, data={
                            'action': 'remove',
                            'task_id': task1.id
                        }
                    )
                    self.assertEqual(rv.status_code, 204)
                    iteration = Iteration(iteration.id)
                    self.assertTrue(task1 not in iteration.tasks)
                    self.assertTrue(task2 in iteration.tasks)

    def test_0050_test_update_iteration(self):
        """
        Test updating iteration
        """
        Iteration = POOL.get('project.iteration')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)
            with Transaction().set_context(company=self.company.id):
                work1, = self.Work.create([{
                    'name': 'ABC Project',
                    'company': self.company.id,
                }])
                project, = self.Project.create([{
                    'work': work1.id,
                    'type': 'project',
                    'state': 'opened',
                    'sequence': 1,
                }])
                self.assert_(project)

                work2, = self.Work.create([{
                    'name': 'User Story',
                    'company': self.company.id,
                }])

                task1, = self.Project.create([{
                    'work': work2.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task1)

                work3, = self.Work.create([{
                    'name': 'User Task',
                    'company': self.company.id,
                }])

                task2, = self.Project.create([{
                    'work': work3.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task2)
                iteration, = Iteration.create([{
                    'name': 'Iteration1',
                    'start_date': datetime.date(2011, 2, 3),
                    'end_date': datetime.date(2011, 2, 5),
                    'tasks': [('add', [task1.id])],
                }])
                self.assert_(iteration)
                with app.test_client() as c:
                    rv = self.login(
                        c, self.scrum_master_user.email, 'password'
                    )
                    # Add task to iteration
                    self.assertEqual(rv.status_code, 302)
                    rv = c.put(
                        '/iterations/%s' % iteration.id, data={
                            'name': 'new_name',
                            'start_date': datetime.date(2011, 2, 3).isoformat(),
                            'end_date': datetime.date(2011, 2, 5).isoformat(),
                        }
                    )
                    self.assertEqual(rv.status_code, 200)
                    iteration = Iteration(iteration.id)
                    self.assertEqual(iteration.name, 'new_name')

    def test_0060_test_delete_iteration(self):
        """
        Test delete iteration
        """
        Iteration = POOL.get('project.iteration')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            app = self.get_app(DEBUG=True)
            with Transaction().set_context(company=self.company.id):
                work1, = self.Work.create([{
                    'name': 'ABC Project',
                    'company': self.company.id,
                }])
                project, = self.Project.create([{
                    'work': work1.id,
                    'type': 'project',
                    'state': 'opened',
                    'sequence': 1,
                }])
                self.assert_(project)

                work2, = self.Work.create([{
                    'name': 'User Story',
                    'company': self.company.id,
                }])

                task1, = self.Project.create([{
                    'work': work2.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task1)

                work3, = self.Work.create([{
                    'name': 'User Task',
                    'company': self.company.id,
                }])

                task2, = self.Project.create([{
                    'work': work3.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task2)
                iteration, = Iteration.create([{
                    'name': 'Iteration1',
                    'start_date': datetime.date(2011, 2, 3),
                    'end_date': datetime.date(2011, 2, 5),
                    'tasks': [('add', [task1.id])],
                }])
                self.assert_(iteration)
                with app.test_client() as c:
                    rv = self.login(
                        c, self.scrum_master_user.email, 'password'
                    )
                    # Add task to iteration
                    self.assertEqual(rv.status_code, 302)
                    rv = c.delete('/iterations/%s' % iteration.id)
                    self.assertEqual(rv.status_code, 204)
                    self.assertFalse(
                        Iteration.search([('id', '=', iteration.id)])
                    )

    def test_0070_test_close_iteration(self):
        """
        Test close iteration
        """
        Iteration = POOL.get('project.iteration')
        ModelData = POOL.get('ir.model.data')
        CloseIteration = POOL.get(
            'project.iteration.close_iteration', type='wizard'
        )

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            self.create_defaults()
            with Transaction().set_context(company=self.company.id):
                work1, = self.Work.create([{
                    'name': 'ABC Project',
                    'company': self.company.id,
                }])
                project, = self.Project.create([{
                    'work': work1.id,
                    'type': 'project',
                    'state': 'opened',
                    'sequence': 1,
                }])
                self.assert_(project)

                work2, = self.Work.create([{
                    'name': 'User Story',
                    'company': self.company.id,
                }])

                task1, = self.Project.create([{
                    'work': work2.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task1)

                work3, = self.Work.create([{
                    'name': 'User Task',
                    'company': self.company.id,
                }])

                task2, = self.Project.create([{
                    'work': work3.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task2)

                work4, = self.Work.create([{
                    'name': 'User Task',
                    'company': self.company.id,
                }])

                task3, = self.Project.create([{
                    'work': work4.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'done',
                }])
                self.assert_(task3)

                work5, = self.Work.create([{
                    'name': 'User Task',
                    'company': self.company.id,
                }])

                task4, = self.Project.create([{
                    'work': work5.id,
                    'type': 'task',
                    'parent': project.id,
                    'state': 'opened',
                }])
                self.assert_(task4)

                old_iteration, = Iteration.create([{
                    'name': 'Iteration1',
                    'start_date': datetime.date(2011, 2, 3),
                    'end_date': datetime.date(2011, 2, 5),
                    'tasks': [('add', [task1.id, task2.id, task3.id])],
                }])
                self.assert_(old_iteration)

                # Create a new iteration
                new_iteration, = Iteration.create([{
                    'name': 'Iteration2',
                    'start_date': datetime.date(2011, 2, 6),
                    'end_date': datetime.date(2011, 2, 9),
                    'tasks': [('add', [task4.id])],
                }])
                self.assert_(new_iteration)

            self.assertEqual(old_iteration.state, 'opened')
            self.assertEqual(len(old_iteration.tasks), 3)
            self.assertEqual(len(old_iteration.backlog_tasks), 0)

            self.assertEqual(new_iteration.state, 'opened')
            self.assertEqual(len(new_iteration.tasks), 1)
            self.assertEqual(len(new_iteration.backlog_tasks), 0)

            with Transaction().set_context(
                    company=self.company.id,
                    active_id=old_iteration.id
            ):
                session_id, start_state, _ = CloseIteration.create()
                close_iteration = CloseIteration(session_id)

                close_iteration.ask.iteration = new_iteration.id

                action_id = ModelData.get_id(
                    'nereid_project', 'act_iteration_form'
                )
                close_iteration.do_close(
                    POOL.get('ir.action.act_window')(action_id)
                )

                self.assertEqual(old_iteration.state, 'closed')
                self.assertEqual(len(old_iteration.tasks), 1)
                self.assertEqual(len(old_iteration.backlog_tasks), 2)

                self.assertEqual(new_iteration.state, 'opened')
                self.assertEqual(len(new_iteration.tasks), 3)
                self.assertEqual(len(new_iteration.backlog_tasks), 0)


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestIteration)
    )
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
