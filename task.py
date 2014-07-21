# -*- coding: utf-8 -*-
"""
    Task

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import calendar
from collections import defaultdict
from datetime import datetime

from nereid import (
    request, abort, render_template, login_required, url_for, redirect,
    flash, jsonify, render_email, permissions_required, route, current_user
)
from nereid.ctx import has_request_context
from nereid.contrib.pagination import Pagination
from trytond.model import ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval
from trytond.config import CONFIG
from trytond import backend


__all__ = ['TaskUsers', 'Task']
__metaclass__ = PoolMeta


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

    description_markup = fields.Selection([
        ('rst', 'reStructuredText'),
        ('markdown', 'Markdown'),
    ], 'Description Markup Type', states={
        'invisible': Eval('type') != 'task',
    }, depends=['type']
    )

    @staticmethod
    def default_description_markup():
        return 'rst'

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

        if not tasks[0].parent.can_write(request.nereid_user, silent=True):
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
    @route('/project-<int:active_id>/task/-new', methods=['GET', 'POST'])
    def create_task(self):
        """Create a new task for the specified project

        POST will create a new task
        """
        NereidUser = Pool().get('nereid.user')
        Activity = Pool().get('nereid.activity')
        Work = Pool().get('timesheet.work')

        project = self.get_project(self.id)

        # Check if user is among the participants
        self.can_write(request.nereid_user)

        if request.method == 'POST':
            if request.is_xhr and request.json:
                name = request.json['name']
            else:
                name = request.form['name']
            data = {
                'parent': self.id,
                'work': Work.create([{
                    'name': name,
                    'company': request.nereid_website.company.id
                }])[0].id,
                'type': 'task',
                'comment': request.form.get('description', None),
            }

            if request.form.getlist('tags', int) and \
                    request.nereid_user.is_admin_of_project(self):
                data['tags'] = [('set', request.form.getlist('tags', int))]

            constraint_start_time = request.form.get(
                'constraint_start_time', None)
            constraint_finish_time = request.form.get(
                'constraint_finish_time', None)
            if constraint_start_time:
                data['constraint_start_time'] = datetime.strptime(
                    constraint_start_time, '%m/%d/%Y')
            if constraint_finish_time:
                data['constraint_finish_time'] = datetime.strptime(
                    constraint_finish_time, '%m/%d/%Y')

            task, = self.create([data])
            Activity.create([{
                'actor': request.nereid_user.id,
                'object_': 'project.work, %d' % task.id,
                'verb': 'created_task',
                'target': 'project.work, %d' % project.id,
                'project': project.id,
            }])

            email_receivers = [p.email for p in self.all_participants]
            if request.form.get('assign_to', None):
                assignee = NereidUser(request.form.get('assign_to', type=int))

                # Check if assignee is among the participants, if not add
                # it to the participants
                if self.can_write(assignee):
                    self.write([task], {
                        'assigned_to': assignee.id,
                        'participants': [
                            ('add', [assignee.id])
                        ]
                    })
                email_receivers = [assignee.email]
            task.send_mail(email_receivers)
            if request.is_xhr:
                return jsonify(task.serialize())
            flash("Task successfully added to project %s" % self.rec_name)
            return redirect(
                url_for(
                    'project.work.render_task',
                    project_id=self.id, task_id=task.id
                )
            )

        flash("Could not create task. Try again.")
        return redirect(request.referrer)

    @login_required
    @route('/task-<int:active_id>/-edit', methods=['POST'])
    def edit_task(self):
        """
        Edit the task
        """
        Activity = Pool().get('nereid.activity')
        Work = Pool().get('timesheet.work')

        task = self.get_task(self.id)

        Work.write([task.work], {
            'name': request.form.get('name'),
        })
        self.write([task], {
            'comment': request.form.get('comment')
        })
        Activity.create([{
            'actor': request.nereid_user.id,
            'object_': 'project.work, %d' % task.id,
            'verb': 'edited_task',
            'target': 'project.work, %d' % task.parent.id,
            'project': task.parent.id,
        }])
        if request.is_xhr:
            return jsonify({
                'success': True,
                'name': self.rec_name,
                'comment': self.comment,
            })
        return redirect(request.referrer)

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

        message = render_email(
            from_email=CONFIG['smtp_from'],
            to=', '.join(receivers),
            subject=subject,
            text_template='project/emails/project_text_content.jinja',
            html_template='project/emails/project_html_content.jinja',
            task=self,
            updated_by=request.nereid_user.display_name
        )

        # Send mail.
        EmailQueue.queue_mail(
            CONFIG['smtp_from'], receivers,
            message.as_string()
        )

    @classmethod
    @route('/task-<int:task_id>/-unwatch', methods=['GET', 'POST'])
    @login_required
    def unwatch(cls, task_id):
        """
        Remove the current user from the participants of the task

        :params task_id: task's id to unwatch.
        """
        task = cls.get_task(task_id)

        if request.nereid_user in task.participants:
            cls.write(
                [task], {
                    'participants': [('unlink', [request.nereid_user.id])]
                }
            )
        if request.is_xhr:
            return jsonify({'success': True})
        return redirect(request.referrer)

    @classmethod
    @route('/task-<int:task_id>/-watch', methods=['GET', 'POST'])
    @login_required
    def watch(cls, task_id):
        """
        Add the current user from the participants of the task

        :params task_id: task's id to watch.
        """
        task = cls.get_task(task_id)

        if request.nereid_user not in task.participants:
            cls.write(
                [task], {
                    'participants': [('add', [request.nereid_user.id])]
                }
            )
        if request.is_xhr:
            return jsonify({'success': True})
        return redirect(request.referrer)

    @classmethod
    @route('/project-<int:project_id>/task-list')
    @login_required
    def render_task_list(cls, project_id):
        """
        Renders a project's task list page
        """
        project = cls.get_project(project_id)
        state = request.args.get('state', None)
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

        counts = {}
        counts['opened_tasks_count'] = cls.search(
            filter_domain + [('state', '=', 'opened')], count=True
        )
        counts['done_tasks_count'] = cls.search(
            filter_domain + [('state', '=', 'done')], count=True
        )
        counts['all_tasks_count'] = cls.search(
            filter_domain, count=True
        )

        if state and state in ('opened', 'done'):
            filter_domain.append(('state', '=', state))

        counts['backlog'] = cls.search(
            filter_domain + [('progress_state', '=', 'Backlog')], count=True
        )
        counts['planning'] = cls.search(
            filter_domain + [('progress_state', '=', 'Planning')], count=True
        )
        counts['in_progress'] = cls.search(
            filter_domain + [('progress_state', '=', 'In Progress')], count=True
        )
        counts['review'] = cls.search(
            filter_domain + [('progress_state', '=', 'Review')], count=True
        )

        if request.is_xhr:
            tasks = cls.search(filter_domain)
            return jsonify({
                'items': map(lambda task: task.serialize('listing'), tasks),
                'domain': filter_domain,
            })

        if state and state == 'opened':
            # Group and return tasks for regular web viewing
            tasks_by_state = defaultdict(list)
            for task in cls.search(filter_domain):
                tasks_by_state[task.progress_state].append(task)
            return render_template(
                'project/task-list-kanban.jinja',
                active_type_name='render_task_list', counts=counts,
                state_filter=state, tasks_by_state=tasks_by_state,
                states=PROGRESS_STATES[:-1], project=project
            )

        tasks = Pagination(cls, filter_domain, page, 20)
        return render_template(
            'project/task-list.jinja', project=project,
            active_type_name='render_task_list', counts=counts,
            state_filter=state, tasks=tasks
        )

    @classmethod
    @route('/my-tasks')
    @login_required
    def my_tasks(cls):
        """
        Renders all tasks of the user in all projects
        """
        state = request.args.get('state', None)

        filter_domain = [
            ('type', '=', 'task'),
        ]
        if request.args.get('watched'):
            # Show all tasks watched, not assigned
            filter_domain.append(('participants', '=', request.nereid_user.id))
        else:
            filter_domain.append(('assigned_to', '=', request.nereid_user.id))
        query = request.args.get('q', None)
        if query:
            # This search is probably the suckiest search in the
            # history of mankind in terms of scalability and utility
            # TODO: Figure out something better
            filter_domain.append(('work.name', 'ilike', '%%%s%%' % query))

        tag = request.args.get('tag', None, int)
        if tag:
            filter_domain.append(('tags', '=', tag))

        counts = {}
        counts['opened_tasks_count'] = cls.search(
            filter_domain + [('state', '=', 'opened')], count=True
        )

        if state and state in ('opened', 'done'):
            filter_domain.append(('state', '=', state))

        tasks = cls.search(filter_domain, order=[('progress_state', 'ASC')])

        if request.is_xhr:
            return jsonify({
                'items': map(lambda task: task.serialize('listing'), tasks),
                'domain': filter_domain,
            })

        # Group and return tasks for regular web viewing
        tasks_by_state = defaultdict(list)
        for task in tasks:
            tasks_by_state[task.progress_state].append(task)
        return render_template(
            'project/global-task-list.jinja',
            active_type_name='render_task_list', counts=counts,
            state_filter=state, tasks_by_state=tasks_by_state,
            states=PROGRESS_STATES[:-1]
        )

    @classmethod
    @route('/project-<int:project_id>/task-<int:task_id>')
    @login_required
    def render_task(cls, task_id, project_id):
        """
        Renders the task in a project
        """
        task = cls.get_task(task_id)

        comments = sorted(
            task.history + task.work.timesheet_lines + task.attachments +
            task.repo_commits, key=lambda x: x.create_date
        )

        hours = {}
        for line in task.work.timesheet_lines:
            hours[line.employee] = hours.setdefault(line.employee, 0) + \
                line.hours

        if request.is_xhr:
            response = cls.serialize(task)
            with Transaction().set_context(task=task_id):
                response['comments'] = [
                    comment.serialize('listing') for comment in comments
                ]
            return jsonify(response)

        return render_template(
            'project/task.jinja', task=task,
            active_type_name='render_task_list', project=task.parent,
            comments=comments, timesheet_summary=hours
        )

    @classmethod
    @route('/tasks-by-employee')
    @login_required
    @permissions_required(perm_any=['project.admin', 'project.manager'])
    def render_tasks_by_employee(cls):
        '''
        Returns rendered task, for employee.
        '''
        open_tasks = cls.search([
            ('state', '=', 'opened'),
            ('assigned_to.employee', '!=', None),
        ], order=[('assigned_to', 'ASC')])
        tasks_by_employee_by_state = defaultdict(lambda: defaultdict(list))
        for task in open_tasks:
            tasks_by_employee_by_state[task.assigned_to][
                task.progress_state
            ].append(task)
        employees = tasks_by_employee_by_state.keys()
        employees.sort()
        return render_template(
            'project/tasks-by-employee.jinja',
            tasks_by_employee_by_state=tasks_by_employee_by_state,
            employees=employees,
            states=PROGRESS_STATES[:-1],
        )

    @classmethod
    @route('/task-<int:task_id>/-update', methods=['GET', 'POST'])
    @login_required
    def update_task(cls, task_id):
        """
        Accepts a POST request against a task_id and updates the ticket

        :param task_id: The ID of the task which needs to be updated
        """
        History = Pool().get('project.work.history')
        TimesheetLine = Pool().get('timesheet.line')
        Activity = Pool().get('nereid.activity')

        task = cls.get_task(task_id)

        history_data = {
            'project': task.id,
            'updated_by': request.nereid_user.id,
            'comment': request.form['comment']
        }

        updatable_attrs = ['progress_state']
        new_participant_ids = set()
        current_participant_ids = [p.id for p in task.participants]
        post_attrs = [request.form.get(attr, None) for attr in updatable_attrs]
        if any(post_attrs):
            # Combined update of task and history since there is some value
            # posted in addition to the comment
            task_changes = {}
            for attr in updatable_attrs:
                if getattr(task, attr) != request.form.get(attr, None):
                    task_changes[attr] = request.form[attr]

            if task_changes.get('progress_state') == 'Done':
                task_changes['state'] = 'done'
            else:
                task_changes['state'] = 'opened'

            new_assignee_id = request.form.get('assigned_to', None, int)
            if new_assignee_id is not None:
                if (new_assignee_id and
                        (not task.assigned_to or
                            new_assignee_id != task.assigned_to.id)) \
                        or (request.form.get('assigned_to', None) == ""):
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
                cls.write([task], task_changes)
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
        Activity.create([{
            'actor': request.nereid_user.id,
            'object_': 'project.work.history, %d' % comment.id,
            'verb': 'updated_task',
            'target': 'project.work, %d' % task.id,
            'project': task.parent.id,
        }])

        if request.nereid_user.id not in current_participant_ids:
            # Add the user to the participants if not already in the list
            new_participant_ids.add(request.nereid_user.id)

        for nereid_user in request.form.getlist('notify[]', int):
            # Notify more people if there are people
            # who havent been added as participants
            if nereid_user not in current_participant_ids:
                new_participant_ids.add(nereid_user)

        if new_participant_ids:
            cls.write([task], {
                'participants': [('add', list(new_participant_ids))]
            })

        hours = request.form.get('hours', None, type=float)
        if hours and request.nereid_user.employee:
            timesheet_line, = TimesheetLine.create([{
                'employee': request.nereid_user.employee.id,
                'hours': hours,
                'work': task.work.id
            }])
            Activity.create([{
                'actor': request.nereid_user.id,
                'object_': 'timesheet.line, %d' % timesheet_line.id,
                'verb': 'reported_time',
                'target': 'project.work, %d' % task.id,
                'project': task.parent.id,
            }])

        # Send the email since all thats required is done
        comment.send_mail()

        if request.is_xhr:
            html = render_template(
                'project/comment.jinja', comment=comment)
            return jsonify({
                'success': True,
                'html': unicode(html),
                'state': task.state,
                'progress_state': task.progress_state,
                'comment': comment.serialize(),
            })
        return redirect(request.referrer)

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
            'actor': request.nereid_user.id,
            'object_': 'project.work.tag, %d' % tag_id,
            'verb': 'added_tag_to_task',
            'target': 'project.work, %d' % task.id,
            'project': task.parent.id,
        }])

        if request.method == 'POST':
            flash('Tag added to task %s' % task.rec_name)
            return redirect(request.referrer)

        flash("Tag cannot be added")
        return redirect(request.referrer)

    @classmethod
    @route(
        '/task-<int:task_id>/tag-<int:tag_id>/-remove', methods=['GET', 'POST']
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
            [task], {'tags': [('unlink', [tag_id])]}
        )
        Activity.create([{
            'actor': request.nereid_user.id,
            'object_': 'project.work, %d' % task.id,
            'verb': 'removed_tag_from_task',
            'target': 'project.work, %d' % task.parent.id,
            'project': task.parent.id,
        }])

        if request.method == 'POST':
            flash('Tag removed from task %s' % task.rec_name)
            return redirect(request.referrer)

        flash("Tag cannot be removed")
        return redirect(request.referrer)

    @classmethod
    @route('/task-<int:task_id>/-mark-time', methods=['GET', 'POST'])
    @login_required
    def mark_time(cls, task_id):
        """
        Marks the time against the employee for the task

        :param task_id: ID of task
        """
        TimesheetLine = Pool().get('timesheet.line')

        if not request.nereid_user.employee:
            flash("Only employees can mark time on tasks!")
            return redirect(request.referrer)

        task = cls.get_task(task_id)

        with Transaction().set_user(0):
            TimesheetLine.create([{
                'employee': request.nereid_user.employee.id,
                'hours': request.form['hours'],
                'work': task.work.id,
            }])

        flash("Time has been marked on task %s" % task.rec_name)
        return redirect(request.referrer)

    @classmethod
    @route('/task-<int:task_id>/-assign', methods=['GET', 'POST'])
    @login_required
    def assign_task(cls, task_id):
        """
        Assign task to a user

        :param task_id: Id of Task
        """
        NereidUser = Pool().get('nereid.user')
        Activity = Pool().get('nereid.activity')

        task = cls.get_task(task_id)

        new_assignee = NereidUser(int(request.form['user']))

        if task.assigned_to == new_assignee:
            flash("Task already assigned to %s" % new_assignee.display_name)
            return redirect(request.referrer)
        if task.parent.can_write(new_assignee):
            cls.write([task], {
                'assigned_to': new_assignee.id,
                'participants': [('add', [new_assignee.id])]
            })
            task.history[-1].send_mail()
            Activity.create([{
                'actor': request.nereid_user.id,
                'object_': 'project.work, %d' % task.id,
                'verb': 'assigned_task_to',
                'target': 'nereid.user, %d' % new_assignee.id,
                'project': task.parent.id,
            }])
            if request.is_xhr:
                return jsonify({
                    'success': True,
                })
            flash("Task assigned to %s" % new_assignee.display_name)
            return redirect(request.referrer)
        flash("Only employees can be assigned to tasks.")
        return redirect(request.referrer)

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

        if request.is_xhr:
            return jsonify({
                'success': True,
            })

        flash("Removed the assigned user from task")
        return redirect(request.referrer)

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

        constraint_start = request.form.get('constraint_start_time', None)
        constraint_finish = request.form.get('constraint_finish_time', None)

        if constraint_start:
            data['constraint_start_time'] = datetime.strptime(
                constraint_start, '%m/%d/%Y')
        if constraint_finish:
            data['constraint_finish_time'] = datetime.strptime(
                constraint_finish, '%m/%d/%Y')

        cls.write([task], data)
        Activity.create([{
            'actor': request.nereid_user.id,
            'object_': 'project.work, %d' % task.id,
            'verb': 'changed_date',
            'project': task.parent.id,
        }])

        if request.is_xhr:
            return jsonify({
                'success': True,
            })

        flash("The constraint dates have been changed for this task.")
        return redirect(request.referrer)

    @classmethod
    @route('/task-<int:task_id>/-delete', methods=['POST'])
    @login_required
    def delete_task(cls, task_id):
        """
        Delete the task from project

        Tasks can be deleted only if
            1. The user is project admin
            2. The user is an admin member in the project

        :param task_id: Id of the task to be deleted
        """
        task = cls.get_task(task_id)

        # Check if user is among the project admins
        if not request.nereid_user.is_admin_of_project(task.parent):
            flash(
                "Sorry! You are not allowed to delete tasks. \
                Contact your project admin for the same."
            )
            return redirect(request.referrer)

        cls.write([task], {'active': False})

        if request.is_xhr:
            return jsonify({
                'success': True,
            })

        flash("The task has been deleted")
        return redirect(
            url_for('project.work.render_project', project_id=task.parent.id)
        )

    @login_required
    @route(
        '/task-<int:active_id>/change-estimated-hours', methods=['GET', 'POST']
    )
    def change_estimated_hours(self):
        """Change estimated hours.

        :param task_id: ID of the task.
        """
        if not request.nereid_user.employee:
            flash("Sorry! You are not allowed to change estimate hours.")
            return redirect(request.referrer)

        estimated_hours = request.form.get(
            'new_estimated_hours', None, type=float
        )
        if estimated_hours:
            self.write([self], {'effort': estimated_hours})
        flash("The estimated hours have been changed for this task.")
        return redirect(request.referrer)
