# -*- coding: utf-8 -*-
"""
    iteration

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: see LICENSE for more details.
"""
from nereid import (
    login_required, url_for, abort, request, route, jsonify, current_user
)
from flask_wtf import Form
from wtforms import IntegerField, SelectField, validators, StringField, \
    DateField
from trytond.model import ModelSQL, ModelView, fields
from trytond.transaction import Transaction
from trytond.pyson import Eval
from trytond.pool import PoolMeta
from nereid.ctx import has_request_context
from nereid.contrib.pagination import Pagination

from task import PROGRESS_STATES

__all__ = ['Iteration', 'IterationBacklog']
__metaclass__ = PoolMeta


class IterationForm(Form):
    "Iteratino Form"
    name = StringField('Name', [validators.DataRequired()])
    start_date = DateField('Start Date', [validators.DataRequired()])
    end_date = DateField('End Date', [validators.DataRequired()])


class IterationAddTaskForm(Form):
    "Iteratino Update Form"
    task_id = IntegerField('Task Id', [validators.DataRequired()])
    action = SelectField(
        'Action to perform', validators=[validators.DataRequired()], choices=[
            ('add', 'Add'),
            ('remove', 'Remove'),
        ]
    )


class Iteration(ModelSQL, ModelView):
    'Iteration'
    __name__ = 'project.iteration'

    name = fields.Char('Name', required=True)
    company = fields.Many2One(
        'company.company', 'Company', select=True, required=True
    )
    start_date = fields.Date('Start Date', required=True, select=True)
    end_date = fields.Date('End Date', required=True, select=True)
    state = fields.Selection([
        ('opened', 'Opened'),
        ('closed', 'Closed'),
    ], 'State', select=True)
    tasks = fields.One2Many(
        'project.work', 'iteration', 'Tasks',
        domain=[
            ('type', '!=', 'project'),
            ('company', '=', Eval('company')),
        ],
        add_remove=[
            ('type', '!=', 'project'),
            ('company', '=', Eval('company')),
        ],
        depends=['company'],
    )
    backlog_tasks = fields.One2Many(
        'project.iteration.backlog', 'iteration', 'Backlog Tasks',
        readonly=True
    )
    url = fields.Function(fields.Char('URL'), 'get_url')

    # Function fields to return status
    count_tasks = fields.Function(fields.Integer("Total Tasks"), 'get_count')
    count_backlog = fields.Function(
        fields.Integer("Tasks in Backlog"), 'get_count'
    )
    count_planning = fields.Function(
        fields.Integer("Tasks in Planning"), 'get_count'
    )
    count_in_progress = fields.Function(
        fields.Integer("Tasks in Progress"), 'get_count'
    )
    count_review = fields.Function(
        fields.Integer("Tasks in Review"), 'get_count'
    )
    count_done = fields.Function(
        fields.Integer("Done Tasks"), 'get_count'
    )

    def get_count(self, name):
        """Get task count based on task state.
        """
        def _get_count(state):
            return len(
                filter(lambda task: task.progress_state == state, self.tasks)
            )

        if name == 'count_backlog':
            return _get_count('Backlog')
        elif name == 'count_planning':
            return _get_count('Planning')
        elif name == 'count_in_progress':
            return _get_count('In Progress')
        elif name == 'count_review':
            return _get_count('Review')
        elif name == 'count_done':
            return len(filter(lambda task: task.state == 'done', self.tasks))
        elif name == 'count_tasks':
            return len(self.tasks + self.backlog_tasks)

    def get_url(self, name):
        """
        Return the url if within an active request context or return None
        :param name: name of field
        """
        if has_request_context():
            return url_for(
                'project.iteration.render', active_id=self.id
            )
        return None

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_state():
        return 'opened'

    @classmethod
    def __setup__(cls):
        super(Iteration, cls).__setup__()
        cls._order.insert(0, ('start_date', 'ASC'))
        cls._error_messages.update({
            'wrong_dates': 'End Date should be greater than Start Date or '
            'Iteration period is overlaping',
        })

    @classmethod
    def validate(cls, iterations):
        """
        Validate iterations
        """
        super(Iteration, cls).validate(iterations)

        for iteration in iterations:
            iteration.check_dates()

    def serialize(self, purpose=None):
        """
        Serialize Iteration
        """
        res = {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'count_tasks': self.count_tasks,
            'count_backlog': self.count_backlog,
            'count_planning': self.count_planning,
            'count_in_progress': self.count_in_progress,
            'count_review': self.count_review,
            'count_done': self.count_done,
        }
        if purpose == "full":
            res.update({
                'tasks': [task.serialize(purpose) for task in self.tasks]
            })
        return res

    def check_dates(self):
        """
        Checks End date should not be less than Start date and,
        Non overlapping of dates for iterations.
        """
        cursor = Transaction().cursor
        table = self.__table__()

        if self.start_date and self.end_date and \
                self.start_date >= self.end_date:
            return False
        cursor.execute(*table.select(
            table.id, where=(((
                    (table.start_date <= self.start_date) &
                    (table.end_date >= self.start_date)) |
                ((table.start_date <= self.end_date) &
                    (table.end_date >= self.end_date)) |
                ((table.start_date >= self.start_date) &
                    (table.end_date <= self.end_date))) &
                (table.id != self.id)
            )
        ))
        return bool(cursor.fetchone())

    @classmethod
    @route("/iterations/", methods=["GET", "POST"])
    @login_required
    def render_list(cls):
        """
        GET: Renders list of iterations.
        POST: Create new iteration.
        """
        if request.method == 'GET':
            page = request.args.get('page', 1, int)
            state = request.args.get('state')

            filter_domain = []
            if state:
                filter_domain.append(('state', '=', state))

            iterations = Pagination(cls, filter_domain, page, 10)
            return jsonify(iterations.serialize())

        if not current_user.has_permissions(['project.scrum_master']):
            # Only get is allowed if user is not scrum_master.
            abort(403)

        create_form = IterationForm()
        if create_form.validate_on_submit():
            iteration, = cls.create([{
                'name': create_form.name.data,
                'start_date': create_form.start_date.data,
                'end_date': create_form.end_date.data,
            }])
            return jsonify({
                'url': iteration.url,
            }), 201

    @route(
        "/iterations/<int:active_id>/stats/tasks_by_user", methods=["GET"]
    )
    @login_required
    def tasks_by_user_stat(self):
        '''
        GET: Return tasks by user
        '''
        res = self.serialize('full')

        tasks_by_user = {}
        for task in res['tasks']:
            tasks_by_user.setdefault(task['owner'], []).append(task)

        del res['tasks']
        res['tasks_by_user'] = tasks_by_user

        return jsonify(res)

    @route(
        "/iterations/<int:active_id>/stats/tasks_by_project", methods=["GET"]
    )
    @login_required
    def tasks_by_project_stat(self):
        '''
        GET: Return tasks by project
        '''
        res = self.serialize('full')

        tasks_by_project = {}
        for task in res['tasks']:
            tasks_by_project.setdefault(task['project'], []).append(task)

        del res['tasks']
        res['tasks_by_project'] = tasks_by_project

        return jsonify(res)

    @route(
        "/iterations/<int:active_id>", methods=["GET", "POST", "PUT", "DELETE"]
    )
    @login_required
    def render(self):
        '''
        GET: Renders an Iteration.
        POST: Add/remove item to Iteration.
        PUT: Update Iteration.
        DELETE: Deletes an Iteration.
        '''
        if request.method == 'GET':
            if not current_user.has_permissions(['project.scrum_master']):
                # TODO: Show render according to user's project permissions
                abort(403)
            return jsonify(self.serialize('full'))

        if self.state != 'opened' or \
                not current_user.has_permissions(['project.scrum_master']):
            # Only 'GET' is allowed if user is not scrum_master or state
            # is not opened
            abort(400)

        add_task_form = IterationAddTaskForm()

        if request.method == 'POST' and add_task_form.validate():
            # Add and remove task from iteration
            if add_task_form.task_id.data \
                    and add_task_form.action.data == 'add':
                self.write([self], {
                    'tasks': [('add', [add_task_form.task_id.data])]
                })
                return jsonify(message='Added successfully')
            if add_task_form.task_id.data \
                    and add_task_form.action.data == 'remove':
                self.write([self], {
                    'tasks': [('remove', [add_task_form.task_id.data])]
                })
                return '', 204  # Removed
            else:
                abort(400)

        update_form = IterationForm(obj=self)

        if request.method == 'PUT' and update_form.validate():
            # Update Iteration
            self.write([self], {
                'name': update_form.name.data,
                'start_date': update_form.start_date.data,
                'end_date': update_form.end_date.data,
            })
            return jsonify(message="Updated successfully")
        if request.method == 'DELETE':
            self.delete([self])
            return "", 204

        # Bad request errors
        if request.method == 'POST':
            return jsonify(errors=add_task_form.errors), 400
        if request.method == 'PUT':
            return jsonify(errors=update_form.errors), 400
        abort(400)


class IterationBacklog(ModelSQL, ModelView):
    "Iteration Backlog"
    __name__ = 'project.iteration.backlog'

    iteration = fields.Many2One(
        'project.iteration', 'Iteration', required=True, select=True
    )
    task = fields.Many2One(
        'project.work', 'Task', required=True, select=True,
        domain=[('type', '=', 'task')]
    )
    progress_state = fields.Selection(
        PROGRESS_STATES, 'Progress State', select=True
    )
    owner = fields.Many2One(
        'nereid.user', 'Task Owner', select=True
    )
    assigned_to = fields.Many2One(
        'nereid.user', 'Assigned To', select=True
    )
    project = fields.Many2One(
        'project.work', 'Project', select=True,
        domain=[('type', '=', 'project')]
    )
