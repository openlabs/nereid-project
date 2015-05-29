# -*- coding: utf-8 -*-
"""
    Task

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import calendar
from datetime import datetime

from nereid import (
    request, abort, login_required, url_for, redirect,
    flash, jsonify, render_email, permissions_required, route, current_user
)
from nereid.ctx import has_request_context
from nereid.contrib.pagination import Pagination
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval
from trytond.config import config
from trytond import backend
from flask_wtf import Form
from wtforms import TextField, SelectField, \
    DateTimeField, IntegerField, SelectMultipleField, validators

__all__ = ['TaskUsers', 'Task']
__metaclass__ = PoolMeta


class CreateTaskForm(Form):
    """Form for creating task.
    """
    project = IntegerField('Project', [validators.DataRequired()])
    name = TextField('Name', [validators.DataRequired()])
    description = TextField('Description')
    subtype = SelectField('SubType', choices=[])
    assign_to = IntegerField('Assign To')
    constraint_start_time = DateTimeField('Constraint Start Time')
    constraint_finish_time = DateTimeField('Constraint Finish Time')
    tags = SelectMultipleField('Tags', choices=[], coerce=int)

    def __init__(self, *args, **kwargs):
        super(CreateTaskForm, self).__init__(*args, **kwargs)

        Work = Pool().get('project.work')

        # Fill subtype choices
        self.subtype.choices = Work.subtype.selection

        # Fill tags choices
        if self.project.data:
            project = Work(self.project.data)
            self.tags.choices = [
                (tag.id, tag.name) for tag in project.tags_for_projects
            ]


calendar.setfirstweekday(calendar.SUNDAY)
PROGRESS_STATES = [
    (None, ''),
    ('Backlog', 'Backlog'),
    ('Planning', 'Planning'),
    ('In Progress', 'In Progress'),
    ('Review', 'Review/QA'),
    ('Done', 'Done'),
]


class TaskUsers(ModelSQL):
    'Task Users'
    __name__ = 'project.work-nereid.user'

    task = fields.Many2One(
        'project.work', 'Task', domain=[('type', '=', 'task')],
        ondelete='CASCADE', select=True, required=True
    )

    user = fields.Many2One(
        'nereid.user', 'User', select=1, required=True
    )

    @classmethod
    def __setup__(cls):
        super(TaskUsers, cls).__setup__()
        cls._sql_constraints += [(
            'check_user',
            'UNIQUE(task, "user")',
            'Users must be unique per project'
        )]

    @classmethod
    def __register__(cls, module_name):
        '''
        Register class and update table name to new.
        '''
        cursor = Transaction().cursor
        TableHandler = backend.get('TableHandler')
        table = TableHandler(cursor, cls, module_name)
        # Migration

        # If column exist, rename it to 'task'
        if table.column_exist('project'):
            table.column_rename('project', 'task')

        super(TaskUsers, cls).__register__(module_name)

        if table.table_exist(cursor, 'project_work_nereid_user_rel'):
            table.table_rename(
                cursor, 'project_work_nereid_user_rel',
                'project_work-nereid_user'
            )


class Task:
    """
    Tryton itself is very flexible in allowing multiple layers of Projects and
    sub projects. But having this and implementing this seems to be too
    convulted for everyday use. So nereid simplifies the process to:

    - Project::Associated to a party
       |
       |-- Task (Type is task)
    """
    __name__ = 'project.work'

    participants = fields.Many2Many(
        'project.work-nereid.user', 'task', 'user',
        'Participants', states={'invisible': Eval('type') != 'task'},
        depends=['type']
    )

    #: Tags for tasks.
    tags = fields.Many2Many(
        'project.work-project.work.tag', 'task', 'tag',
        'Tags', depends=['type'],
        states={
            'invisible': Eval('type') != 'task',
            'readonly': Eval('type') != 'task',
        }
    )

    all_participants = fields.Function(
        fields.One2Many(
            'nereid.user', None,
            'All Participants', depends=['company']
        ), 'get_all_participants'
    )
    assigned_to = fields.Many2One(
        'nereid.user', 'Assigned to', depends=['all_participants'],
        domain=[('id', 'in', Eval('all_participants'))],
        states={
            'invisible': Eval('type') != 'task',
            'readonly': Eval('type') != 'task',
        }
    )

    progress_state = fields.Selection(
        PROGRESS_STATES, 'Progress State',
        depends=['state', 'type'], select=True,
        states={
            'invisible':
            (Eval('type') != 'task') | (Eval('state') != 'opened'),
            'readonly':
            (Eval('type') != 'task') | (Eval('state') != 'opened'),
        }
    )

    owner = fields.Many2One(
        'nereid.user', 'Task Owner', depends=['all_participants'],
        domain=[('id', 'in', Eval('all_participants'))],
        states={
            'invisible': Eval('type') != 'task',
        }
    )

    description_markup = fields.Selection([
        (None, 'Plain text'),
        ('rst', 'reStructuredText'),
        ('markdown', 'Markdown'),
    ], 'Description Markup Type', states={
        'invisible': Eval('type') != 'task',
    }, depends=['type']
    )

    @staticmethod
    def default_description_markup():
        return 'markdown'

    @staticmethod
    def default_progress_state():
        '''
        Default for progress state
        '''
        return 'Backlog'

    def get_all_participants(self, name):
        """
        Returns all the nereid user which are participants in the project
        """
        if self.parent:
            users = [p.id for p in self.parent.all_participants]
        else:
            users = [member.user.id for member in self.members]

        return list(set(users))

    @classmethod
    def create(cls, vlist):
        '''
        Create a Task and add current user as participant of the project

        :param vlist: List of dictionaries of values to create
        '''
        for values in vlist:
            if has_request_context():
                if values['type'] == 'task' and not current_user.is_anonymous():
                    values.setdefault('participants', []).append(
                        ('add', [current_user.id])
                    )
            else:
                # TODO: identify the nereid user through employee
                pass
        return super(Task, cls).create(vlist)

    @classmethod
    def get_task(cls, task_id):
        """
        Common base for fetching the task while validating if the user
        can use it.

        :param task_id: Task Id of project to fetch.
        """
        tasks = cls.search([
            ('id', '=', task_id),
            ('type', '=', 'task'),
        ])

        if not tasks:
            raise abort(404)

        if not tasks[0].parent.can_write(current_user, silent=True):
            # If the user is not allowed to access this project then dont let
            raise abort(403)

        return tasks[0]

    @classmethod
    def get_tasks_by_tag(cls, tag_id):
        """
        Return the tasks associated with a tag

        :param tag_id: tag Id of which tasks to fetch.
        """
        TaskTags = Pool().get('project.work-project.work.tag')

        tasks = map(int, TaskTags.search([
            ('tag', '=', tag_id),
            ('task.state', '=', 'opened'),
        ]))
        return tasks

    @login_required
    @route('/tasks/<int:active_id>', methods=['GET'])
    def get_basic_data(self):
        """
        If the user only has a task ID, then return some basic information
        to the user.
        """
        task = self.get_task(self.id)
        return jsonify(task.serialize())

    @login_required
    @route('/projects/<int:active_id>/tasks/', methods=['GET', 'POST'])
    def create_task(self):
        """Create a new task for the specified project

        POST will create a new task
        """
        NereidUser = Pool().get('nereid.user')
        Activity = Pool().get('nereid.activity')
        Work = Pool().get('timesheet.work')
        Task = Pool().get('project.work')

        # Check if user has write permissions in project.
        if not self.can_write(current_user, silent=True):
            return abort(403)

        project = self.get_project(self.id)
        form = CreateTaskForm(project=project.id)

        if form.validate_on_submit():
            work, = Work.create([{
                'name': form.name.data,
                'company': request.nereid_website.company.id
            }])
            task = Task()
            task.parent = self
            task.work = work
            task.type = 'task'
            task.subtype = form.subtype.data
            task.comment = form.description.data

            if current_user.is_admin_of_project(self) and form.tags.data:
                task.tags = form.tags.data

            if form.constraint_start_time.data:
                task.constraint_start_time = form.constraint_start_time.data

            if form.constraint_finish_time.data:
                task.constraint_finish_time = form.constraint_finish_time.data

            if form.assign_to.data:
                assigned_to = NereidUser(form.assign_to.data)

                if self.can_write(assigned_to):
                    task.assigned_to = assigned_to.id

            task.save()

            Activity.create([{
                'actor': current_user.id,
                'object_': 'project.work, %d' % task.id,
                'verb': 'created_task',
                'target': 'project.work, %d' % project.id,
                'project': project.id,
            }])

            task.send_mail([p.email for p in self.all_participants])

            return jsonify(task.serialize()), 201

        elif form.errors:
            return jsonify({
                'errors': form.errors,
                'message': 'Task creation has been failed',
            }), 400

        page = request.args.get('page', 1, int)
        filter_domain = [
            ('type', '=', 'task'),
            ('parent', '=', project.id),
        ]

        query = request.args.get('q', None)
        if query:
            # This search is probably the suckiest search in the
            # history of mankind in terms of scalability and utility
            # TODO: Figure out something better
            filter_domain.append(('work.name', 'ilike', '%%%s%%' % query))

        tag = request.args.get('tag', None, int)
        if tag:
            filter_domain.append(('tags', '=', tag))

        if request.args.get('user') == 'no one':
            filter_domain.append(('assigned_to', '=', None))
        elif request.args.get('user', None, int):
            filter_domain.append(
                ('assigned_to', '=', request.args.get('user', None, int))
            )

        state = request.args.get('state', None)
        if state and state in ('opened', 'done'):
            filter_domain.append(('state', '=', state))

        per_page = min(request.args.get('per_page', 50, int), 50)
        tasks = Pagination(
            Task, filter_domain, page, per_page
        )

        return jsonify(tasks.serialize(purpose='listing'))

    @login_required
    @route(
        '/projects/<int:project_id>/tasks/<int:active_id>/',
        methods=['GET', 'POST', 'DELETE']
    )
    def render_task(self, project_id):
        """Render task
        """
        Activity = Pool().get('nereid.activity')
        Work = Pool().get('timesheet.work')

        # TODO: check if task belong to same project.
        task = self.get_task(self.id)

        if request.method == "POST":
            Work.write([task.work], {
                'name': request.json.get('name'),
            })
            self.write([task], {
                'comment': request.json.get('comment')
            })
            Activity.create([{
                'actor': current_user.id,
                'object_': 'project.work, %d' % task.id,
                'verb': 'edited_task',
                'target': 'project.work, %d' % task.parent.id,
                'project': task.parent.id,
            }])
            return jsonify(message="Task has been edited successfully")

        elif request.method == "DELETE":
            # Check if user is among the project admins
            if not current_user.is_admin_of_project(task.parent):
                abort(403)

            self.active = False
            self.save()

            return "", 204

        comments = sorted(
            task.history + task.work.timesheet_lines + task.attachments +
            task.repo_commits, key=lambda x: x.create_date
        )

        response = task.serialize()
        with Transaction().set_context(task=self.id):
            response['comments'] = [
                comment.serialize('listing') for comment in comments
            ]

        return jsonify(response)

    def send_mail(self, receivers=None):
        """Send mail when task created.

        :param receivers: Receivers of email.
        """
        EmailQueue = Pool().get('email.queue')

        subject = "[#%s %s] - %s" % (
            self.id, self.parent.rec_name, self.rec_name
        )

        if not receivers:
            receivers = [
                p.email for p in self.participants if p.email
            ]
        if self.created_by.email in receivers:
            receivers.remove(self.created_by.email)

        if not receivers:
            return

        sender = config.get('email', 'from')

        message = render_email(
            from_email=sender,
            to=', '.join(receivers),
            subject=subject,
            text_template='project/emails/project_text_content.jinja',
            html_template='project/emails/project_html_content.jinja',
            task=self,
            updated_by=current_user.display_name
        )

        # Send mail.
        EmailQueue.queue_mail(
            sender, receivers, message.as_string()
        )

    @route('/tasks/<int:active_id>/watch', methods=['PUT'])
    @login_required
    def watch(self):
        """
        PUT /tasks/:task_id/watch
        Param {
            action: watch, unwatch
        }
        """
        task = self.get_task(self.id)

        if request.json.get('action') == 'watch':
            if current_user not in task.participants:
                self.write(
                    [task], {
                        'participants': [('add', [current_user.id])]
                    }
                )
                return jsonify({'message': "Successfully watched"}), 200

        elif request.json.get('action') == 'unwatch':
            if current_user in task.participants:
                self.write(
                    [task], {
                        'participants': [('remove', [current_user.id])]
                    }
                )
                return jsonify({'message': "Successfully unwatched"}), 200

        return jsonify({'message': "Invalid action"}), 400

    @classmethod
    @route('/users/<int:user_id>/tasks/', methods=['GET'])
    @login_required
    def my_tasks(cls, user_id):
        """
        TODO: Move this to user model and make it instance method.

        Renders all tasks of the user in all projects
        """
        state = request.args.get('state', None)

        # TODO: this method also takes user_id, this will be helpful for
        # public/private tasks in future.
        #
        # Check if user_id is valid!

        filter_domain = [
            ('type', '=', 'task'),
        ]

        project = request.args.get('project', None, int)
        if project:
            # Only show tasks in the specified project
            filter_domain.append(('parent', '=', project))
        if request.args.get('watched'):
            # Show all tasks watched, not assigned
            filter_domain.append(('participants', '=', current_user.id))
        else:
            filter_domain.append(('assigned_to', '=', current_user.id))
        query = request.args.get('q', None)
        if query:
            # This search is probably the suckiest search in the
            # history of mankind in terms of scalability and utility
            # TODO: Figure out something better
            filter_domain.append(('work.name', 'ilike', '%%%s%%' % query))

        tag = request.args.get('tag', None, int)
        if tag:
            filter_domain.append(('tags', '=', tag))

        if state and state in ('opened', 'done'):
            filter_domain.append(('state', '=', state))

        tasks = cls.search(filter_domain, order=[('progress_state', 'ASC')])

        return jsonify(items=[task.serialize('listing') for task in tasks])

    @classmethod
    @route('/open-tasks')
    @login_required
    @permissions_required(perm_any=['project.admin', 'project.manager'])
    def render_open_tasks(cls):
        '''
        Returns all open tasks, employees and projects. This is useful for
        project admins and managers to splice and view open work from different
        angles.
        '''
        open_tasks = cls.search([
            ('state', '=', 'opened'),
            ('type', '=', 'task'),
        ], order=[('assigned_to', 'ASC')])

        users = set([])
        projects = set([])
        for task in open_tasks:
            if task.assigned_to:
                users.add(task.assigned_to)
            projects.add(task.project)

        employees = set([])
        for user in users:
            if user is not None and user.employee:
                employees.add(user)

        return jsonify(
            tasks=[task.serialize('listing') for task in open_tasks],
            users=[user.serialize() for user in users],
            employees=[employee.serialize() for employee in employees],
            projects=[project.serialize() for project in projects],
        )

    @route(
        '/projects/<int:project_id>/tasks/<int:active_id>/updates/',
        methods=['GET', 'POST']
    )
    @login_required
    def update_task(self, project_id):
        """
        Accepts a POST request against a task_id and updates the ticket

        """
        History = Pool().get('project.work.history')
        TimesheetLine = Pool().get('timesheet.line')
        Activity = Pool().get('nereid.activity')

        task = self.get_task(self.id)

        if request.method == "GET":
            comments = sorted(
                task.history + task.work.timesheet_lines + task.attachments +
                task.repo_commits, key=lambda x: x.create_date
            )
            return jsonify(
                items=[comment.serialize('listing') for comment in comments]
            )

        history_data = {
            'project': task.id,
            'updated_by': current_user.id,
            'comment': request.json.get('comment'),
        }

        updatable_attrs = ['progress_state']
        new_participant_ids = set()
        current_participant_ids = [p.id for p in task.participants]
        post_attrs = [
            request.json.get(attr, None) for attr in updatable_attrs
        ]
        if any(post_attrs):
            # Combined update of task and history since there is some value
            # posted in addition to the comment
            task_changes = {}
            for attr in updatable_attrs:
                if getattr(task, attr) != request.json.get(attr, None):
                    task_changes[attr] = request.json.get(attr)

            if task_changes.get('progress_state') == 'Done':
                task_changes['state'] = 'done'
            else:
                task_changes['state'] = 'opened'

            new_assignee_id = request.json.get('assigned_to', None)
            if new_assignee_id is not None:
                if (new_assignee_id and
                        (not task.assigned_to or
                            new_assignee_id != task.assigned_to.id)) \
                        or (request.json.get('assigned_to', None) == ""):
                        # Clear the user
                    history_data['previous_assigned_to'] = \
                        task.assigned_to and task.assigned_to.id or None
                    history_data['new_assigned_to'] = new_assignee_id
                    task_changes['assigned_to'] = new_assignee_id
                    if new_assignee_id and new_assignee_id not in \
                            current_participant_ids:
                        new_participant_ids.add(new_assignee_id)
            if task_changes:
                # Only write change if anything has really changed
                self.write([task], task_changes)
                comment = task.history[-1]
                History.write([comment], history_data)
            else:
                # just create comment since nothing really changed since this
                # update. This is to cover to cover cases where two users who
                # havent refreshed the web page close the ticket
                comment, = History.create([history_data])
        else:
            # Just comment, no update to task
            comment, = History.create([history_data])
        # `items` to serialize and send to client like comment, state change.
        items = []
        Activity.create([{
            'actor': current_user.id,
            'object_': 'project.work.history, %d' % comment.id,
            'verb': 'updated_task',
            'target': 'project.work, %d' % task.id,
            'project': task.parent.id,
        }])
        items.append(comment)

        if current_user.id not in current_participant_ids:
            # Add the user to the participants if not already in the list
            new_participant_ids.add(current_user.id)

        for nereid_user in request.json.get('notify', []):
            # Notify more people if there are people
            # who havent been added as participants
            if nereid_user not in current_participant_ids:
                new_participant_ids.add(nereid_user)

        if new_participant_ids:
            self.write([task], {
                'participants': [('add', list(new_participant_ids))]
            })

        hours = float(request.json.get('hours', 0)) or None
        if hours and current_user.employee:
            timesheet_line, = TimesheetLine.create([{
                'employee': current_user.employee.id,
                'hours': hours,
                'work': task.work.id
            }])
            Activity.create([{
                'actor': current_user.id,
                'object_': 'timesheet.line, %d' % timesheet_line.id,
                'verb': 'reported_time',
                'target': 'project.work, %d' % task.id,
                'project': task.parent.id,
            }])
            items.append(timesheet_line)

        # Send the email since all thats required is done
        comment.send_mail()

        return jsonify(
            items=[activity.serialize() for activity in items]
        ), 201

    @classmethod
    @route('/task-<int:task_id>/tag-<int:tag_id>/-add', methods=['GET', 'post'])
    @login_required
    def add_tag(cls, task_id, tag_id):
        """
        Assigns the provided to this task

        :param task_id: ID of task
        :param tag_id: ID of tag
        """
        Activity = Pool().get('nereid.activity')
        task = cls.get_task(task_id)

        cls.write(
            [task], {'tags': [('add', [tag_id])]}
        )
        Activity.create([{
            'actor': current_user.id,
            'object_': 'project.work.tag, %d' % tag_id,
            'verb': 'added_tag_to_task',
            'target': 'project.work, %d' % task.id,
            'project': task.parent.id,
        }])

        if request.method == 'POST':
            return jsonify(message='Tag added to task %s' % task.rec_name)

        return jsonify(message="Tag cannot be added")

    @classmethod
    @route(
        '/task-<int:task_id>/tag-<int:tag_id>/-remove', methods=['POST']
    )
    @login_required
    def remove_tag(cls, task_id, tag_id):
        """
        Assigns the provided to this task

        :param task_id: ID of task
        :param tag_id: ID of tag
        """
        Activity = Pool().get('nereid.activity')
        task = cls.get_task(task_id)

        cls.write(
            [task], {'tags': [('remove', [tag_id])]}
        )
        Activity.create([{
            'actor': current_user.id,
            'object_': 'project.work, %d' % task.id,
            'verb': 'removed_tag_from_task',
            'target': 'project.work, %d' % task.parent.id,
            'project': task.parent.id,
        }])

        return jsonify(message='Tag removed from task %s' % task.rec_name)

    @route('/tasks/<int:active_id>/mark-time', methods=['POST'])
    @login_required
    def mark_time(self):
        """
        POST /tasks/:id/mark-time
            Param: hours
        """
        TimesheetLine = Pool().get('timesheet.line')

        if not current_user.employee:
            abort(403)

        task = self.get_task(self.id)

        if request.json.get('hours'):
            with Transaction().set_user(0):
                TimesheetLine.create([{
                    'employee': current_user.employee.id,
                    'hours': request.json.get('hours'),
                    'work': task.work.id,
                }])
            return jsonify(message="Time marked successfully")

        return jsonify(message="Invaild time"), 400

    @route('/tasks/<int:active_id>/assign', methods=['POST'])
    @login_required
    def assign_task(self):
        """
        POST /tasks/:id/assign
            Param: user
        """
        NereidUser = Pool().get('nereid.user')
        Activity = Pool().get('nereid.activity')

        task = self.get_task(self.id)

        if not request.json.get('user'):
            return jsonify(message="Invalid user"), 400

        new_assignee = NereidUser(int(request.json.get('user')))

        if task.assigned_to == new_assignee:
            return jsonify(message="Task already assigned to user"), 400

        if task.parent.can_write(new_assignee):
            self.write([task], {
                'assigned_to': new_assignee.id,
                'participants': [('add', [new_assignee.id])]
            })
            task.history[-1].send_mail()
            Activity.create([{
                'actor': current_user.id,
                'object_': 'project.work, %d' % task.id,
                'verb': 'assigned_task_to',
                'target': 'nereid.user, %d' % new_assignee.id,
                'project': task.parent.id,
            }])
            return jsonify(message="Task has been assigned to user"), 200

        abort(403)

    @classmethod
    @route('/task-<int:task_id>/-remove-assign', methods=['POST'])
    @login_required
    def clear_assigned_user(cls, task_id):
        """Clear the assigned user from the task

        :param task_id: Id of Task
        """
        task = cls.get_task(task_id)

        cls.write([task], {
            'assigned_to': None
        })

        return jsonify({
            "message": "Removed the assigned user from task",
        })

    @classmethod
    @route('/task-<int:task_id>/change_constraint_dates', methods=['POST'])
    @login_required
    def change_constraint_dates(cls, task_id):
        """
        Change the constraint dates
        """
        Activity = Pool().get('nereid.activity')

        task = cls.get_task(task_id)

        data = {
            'constraint_start_time': False,
            'constraint_finish_time': False
        }

        constraint_start = request.json.get('constraint_start_time', None)
        constraint_finish = request.json.get('constraint_finish_time', None)

        if constraint_start:
            data['constraint_start_time'] = datetime.strptime(
                constraint_start, '%m/%d/%Y')
        if constraint_finish:
            data['constraint_finish_time'] = datetime.strptime(
                constraint_finish, '%m/%d/%Y')

        cls.write([task], data)
        Activity.create([{
            'actor': current_user.id,
            'object_': 'project.work, %d' % task.id,
            'verb': 'changed_date',
            'project': task.parent.id,
        }])

        return jsonify({
            'message': "The constraint dates have been changed for this task.",
        })

    @login_required
    @route(
        '/task-<int:active_id>/change-estimated-hours', methods=['GET', 'POST']
    )
    def change_estimated_hours(self):
        """Change estimated hours.

        :param task_id: ID of the task.
        """
        if not current_user.employee:
            flash("Sorry! You are not allowed to change estimate hours.")
            return redirect(request.referrer)

        estimated_hours = float(request.json.get('new_estimated_hours', 0)) \
            or None
        if estimated_hours:
            self.write([self], {'effort': estimated_hours})
        flash("The estimated hours have been changed for this task.")
        return redirect(request.referrer)

    @route(
        '/task-<int:active_id>/move-to-project-<int:project_id>',
        methods=['POST']
    )
    @login_required
    @permissions_required(perm_any=['project.admin', 'project.manager'])
    def move_task_to_project(self, project_id):
        """
        Move task from one project to another.
        """
        ProjectWork = Pool().get('project.work')

        assert self.type == 'task'

        try:
            target_project, = ProjectWork.search([
                ('id', '=', project_id),
                ('type', '=', 'project')
            ], limit=1)
        except ValueError:
            flash("No project found with given details")
            return redirect(request.referrer)

        if not (
            current_user.is_admin_of_project(self.parent) and
            current_user.is_admin_of_project(target_project)
        ):
            abort(403)

        if self.parent.id == target_project.id:
            flash("Task already in this project")
            return redirect(request.referrer)

        if self.assigned_to not in [
            member.user for member in target_project.members
        ]:
            self.assigned_to = None

        # Move task to target project
        self.parent = target_project.id
        self.save()

        flash("Task #%d successfully moved to project %s" % (
            self.id, target_project.work.name
        ))
        return redirect(
            url_for(
                'project.work.render_task',
                project_id=target_project.id, active_id=self.id
            )
        )
