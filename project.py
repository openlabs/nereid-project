# -*- coding: utf-8 -*-
"""
    project

    Extend the project to allow users

    :copyright: (c) 2012 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import tempfile
import random
import string
import warnings
from datetime import datetime
from itertools import groupby, chain
from mimetypes import guess_type

from nereid import (request, abort, render_template, login_required, url_for,
    redirect, flash, jsonify, render_email)
from flask import send_file
from nereid.ctx import has_request_context
from nereid.signals import registration
from nereid.contrib.pagination import Pagination
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.config import CONFIG
from trytond.tools import get_smtp_server


class WebSite(ModelSQL, ModelView):
    """
    Website
    """
    _name = "nereid.website"

    @login_required
    def home(self):
        """
        Put recent projects into the home
        """
        user_obj = Pool().get('nereid.user')
        project_obj = Pool().get('project.work')

        # TODO: Limit to the last 5 projects
        if user_obj.is_project_admin(request.nereid_user):
            project_ids = project_obj.search([
                ('type', '=', 'project'),
                ('parent', '=', False),
            ])
        else:
            project_ids = project_obj.search([
                ('participants', '=', request.nereid_user.id),
                ('type', '=', 'project'),
                ('parent', '=', False),
            ])
        projects = project_obj.browse(project_ids)
        return render_template('home.jinja', projects=projects)

WebSite()


class ProjectUsers(ModelSQL):
    _name = 'project.work-nereid.user'
    _table = 'project_work_nereid_user_rel'

    project = fields.Many2One(
        'project.work', 'Project',
        ondelete='CASCADE', select=1, required=True)

    user = fields.Many2One(
        'nereid.user', 'User', select=1, required=True
    )

ProjectUsers()


class ProjectInvitation(ModelSQL, ModelView):
    "Project Invitation store"
    _name = 'project.work.invitation'
    _description = __doc__

    email = fields.Char('Email', required=True, select=True)
    invitation_code = fields.Char(
        'Invitation Code', select=True
    )
    nereid_user = fields.Many2One('nereid.user', 'Nereid User')
    project = fields.Many2One('project.work', 'Project')

    def create(self, vals):
        existing_invite = self.search([
            ('invitation_code', '=', vals['invitation_code'])
        ])
        if existing_invite:
            vals['invitation_code'] = ''.join(
                random.sample(string.letters + string.digits, 20)
            )

        return super(ProjectInvitation, self).create(vals)

ProjectInvitation()


class ProjectWorkInvitation(ModelSQL):
    "Project Work Invitation"
    _name = 'project.work-project.invitation'
    _description = __doc__

    invitation = fields.Many2One(
        'project.work.invitation', 'Invitation',
        ondelete='CASCADE', select=1, required=True
    )
    project = fields.Many2One(
        'project.work.invitation', 'Project',
        ondelete='CASCADE', select=1, required=True
    )

ProjectWorkInvitation()


class Project(ModelSQL, ModelView):
    """
    Tryton itself is very flexible in allowing multiple layers of Projects and
    sub projects. But having this and implementing this seems to be too
    convulted for everyday use. So nereid simplifies the process to:

    - Project::Associated to a party
       |
       |-- Task (Type is task)
    """
    _name = 'project.work'

    history = fields.One2Many('project.work.history', 'project',
        'History', readonly=True)
    participants = fields.Many2Many(
        'project.work-nereid.user', 'project', 'user',
        'Participants'
    )

    tags_for_projects = fields.One2Many('project.work.tag', 'project',
        'Tags', states={
            'invisible': Eval('type') != 'project',
            'readonly': Eval('type') != 'project',
        }
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

    created_by = fields.Many2One('nereid.user', 'Created by')

    all_participants = fields.Function(
        fields.Many2Many(
            'project.work-nereid.user', 'project', 'user',
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

    #: Get all the attachments on the object and return them
    attachments = fields.Function(
        fields.One2Many('ir.attachment', None, 'Attachments'),
        'get_attachments'
    )

    #TODO: Add a field for computed state

    def __init__(self):
        super(Project, self).__init__()
        self._order.insert(0, ('id', 'DESC'))

    @login_required
    def home(self):
        """
        Put recent projects into the home
        """
        user_obj = Pool().get('nereid.user')
        project_obj = Pool().get('project.work')

        # TODO: Limit to the last 5 projects
        if user_obj.is_project_admin(request.nereid_user):
            project_ids = project_obj.search([
                ('type', '=', 'project'),
                ('parent', '=', False),
            ])
        else:
            project_ids = project_obj.search([
                ('participants', '=', request.nereid_user.id),
                ('type', '=', 'project'),
                ('parent', '=', False),
            ])
        projects = project_obj.browse(project_ids)
        return render_template('project/home.jinja', projects=projects)

    def get_attachments(self, ids, name=None):
        """
        Return all the attachments in the object
        """
        attachment_obj = Pool().get('ir.attachment')

        vals = {}
        for project_id in ids:
            attachments = attachment_obj.search([
                ('resource', '=', '%s,%d' % (self._name, project_id))
            ])
            vals[project_id] = attachments
        return vals

    def get_all_participants(self, ids, name=None):
        """
        All participants includes the participants in the project and also
        the admins
        """
        vals = {}
        for work in self.browse(ids):
            vals[work.id] = []
            vals[work.id].extend([p.id for p in work.participants])
            vals[work.id].extend([p.id for p in work.company.project_admins])
            if work.parent:
                vals[work.id].extend(
                    [p.id for p in work.parent.all_participants]
                )
            vals[work.id] = list(set(vals[work.id]))
        return vals

    def create(self, values):
        if has_request_context():
            values['created_by'] = request.nereid_user.id
            if values['type'] == 'task':
                values.setdefault('participants', [])
                values['participants'].append(
                    ('add', [request.nereid_user.id])
                )
        else:
            # TODO: identify the nereid user through employee
            pass
        return super(Project, self).create(values)

    def can_read(self, project, user):
        """
        Returns true if the given nereid user can read the project

        :param project: The browse record of the project
        :param user: The browse record of the current nereid user
        """
        nereid_user_obj = Pool().get('nereid.user')

        if nereid_user_obj.is_project_admin(user):
            return True
        if not user in project.participants:
            raise abort(404)
        return True

    def can_write(self, project, user):
        """
        Returns true if the given user can write to the project

        :param project: The browse record of the project
        :param user: The browse record of the current nereid user
        """
        nereid_user_obj = Pool().get('nereid.user')

        if nereid_user_obj.is_project_admin(user):
            return True
        if not user in project.participants:
            raise abort(404)
        return True

    def get_project(self, project_id):
        """
        Common base for fetching the project while validating if the user
        can use it.

        :param project_id: ID of the project
        """
        project = self.search([
            ('id', '=', project_id),
            ('type', '=', 'project'),
        ])

        if not project:
            raise abort(404)

        project = self.browse(project[0])

        if not self.can_read(project, request.nereid_user):
            # If the user is not allowed to access this project then dont let
            raise abort(404)

        return project

    def get_task(self, task_id):
        """
        Common base for fetching the task while validating if the user
        can use it.

        :param task_id: ID of the task
        """
        task = self.search([
            ('id', '=', task_id),
            ('type', '=', 'task'),
        ])

        if not task:
            raise abort(404)

        task = self.browse(task[0])

        if not self.can_write(task.parent, request.nereid_user):
            # If the user is not allowed to access this project then dont let
            raise abort(403)

        return task

    def get_tasks_by_tag(self, tag_id):
        """Return the tasks associated with a tag
        """
        task_tag_obj = Pool().get('project.work-project.work.tag')
        tasks = task_tag_obj.search([
            ('tag', '=', tag_id),
            ('task.state', '=', 'opened'),
        ])
        return tasks

    @login_required
    def render_project(self, project_id):
        """
        Renders a project
        """
        project = self.get_project(project_id)
        return render_template(
            'project/project.jinja', project=project, active_type_name="recent"
        )

    @login_required
    def create_project(self):
        """Create a new project

        POST will create a new project
        """
        if not request.nereid_user.is_project_admin(request.nereid_user):
            flash("Sorry! You are not allowed to create new projects. \
                Contact your project admin for the same.")
            return redirect(request.referrer)

        if request.method == 'POST':
            project_id = self.create({
                'name': request.form['name'],
                'type': 'project',
            })
            flash("Project successfully created.")
            return redirect(
                url_for('project.work.render_project', project_id=project_id)
            )

        flash("Could not create project. Try again.")
        return redirect(request.referrer)

    @login_required
    def create_task(self, project_id):
        """Create a new task for the specified project

        POST will create a new task
        """
        nereid_user_obj = Pool().get('nereid.user')
        project = self.get_project(project_id)
        # Check if user is among the participants
        self.can_write(project, request.nereid_user)

        if request.method == 'POST':
            task_id = self.create({
                'parent': project_id,
                'name': request.form['name'],
                'type': 'task',
                'comment': request.form.get('description', False),
            })
            email_receivers = [p.email for p in project.all_participants]
            if request.form.get('assign_to', False):
                assignee = nereid_user_obj.browse(
                    int(request.form.get('assign_to'))
                )
                self.write(task_id, {
                    'assigned_to': assignee.id,
                    'participants': [
                        ('add', [assignee.id])
                    ]
                })
                email_receivers = [assignee.email]
            flash("Task successfully added to project %s" % project.name)
            self.send_mail(task_id, email_receivers)
            return redirect(
                url_for('project.work.render_task',
                    project_id=project_id, task_id=task_id
                )
            )

        flash("Could not create task. Try again.")
        return redirect(request.referrer)

    def send_mail(self, task_id, receivers=None):
        """Send mail when task created.

        :param task_id: ID of task
        :param receivers: Receivers of email.
        """
        task = self.browse(task_id)

        subject = "[%s] - %s" % (task.parent.name, task.name)

        if not receivers:
            receivers = [s.email for s in task.participants
                         if s.email]

        message = render_email(
            from_email=CONFIG['smtp_from'],
            to=', '.join(receivers),
            subject=subject,
            text_template='project/emails/project_text_content.jinja',
            html_template='project/emails/project_html_content.jinja',
            task=task,
            updated_by=request.nereid_user.name
        )

        #Send mail.
        server = get_smtp_server()
        server.sendmail(CONFIG['smtp_from'], receivers,
            message.as_string())
        server.quit()

    @login_required
    def unwatch(self, task_id):
        """
        Remove the current user from the participants of the task

        :param task_id: Id of the task
        """
        task = self.get_task(task_id)

        if request.nereid_user in task.participants:
            self.write(
                task.id, {
                    'participants': [('unlink', [request.nereid_user.id])]
                }
            )
        if request.is_xhr:
            return jsonify({'success': True})
        return redirect(request.referrer)

    @login_required
    def watch(self, task_id):
        """
        Add the current user from the participants of the task

        :param task_id: Id of the task
        """
        task = self.get_task(task_id)

        if request.nereid_user not in task.participants:
            self.write(
                task.id, {
                    'participants': [('add', [request.nereid_user.id])]
                }
            )
        if request.is_xhr:
            return jsonify({'success': True})
        return redirect(request.referrer)

    @login_required
    def permissions(self, project_id):
        """
        Permissions for the project
        """
        project = self.get_project(project_id)
        return render_template(
            'project/permissions.jinja', project=project,
            active_type_name='permissions'
        )

    @login_required
    def projects_list(self, page=1):
        """
        Render a list of projects
        """
        projects = self.search([
            ('party', '=', request.nereid_user.party),
        ])
        return render_template('project/projects.jinja', projects=projects)

    @login_required
    def invite(self, project_id):
        """Invite a user via email to the project

        :param project_id: ID of Project
        """
        nereid_user_obj = Pool().get('nereid.user')
        project_invitation_obj = Pool().get('project.work.invitation')
        data_obj = Pool().get('ir.model.data')

        if not request.method == 'POST':
            return abort(404)

        project = self.get_project(project_id)

        email = request.form['email']

        existing_user_id = nereid_user_obj.search([
            ('email', '=', email),
            ('company', '=', request.nereid_website.company.id),
        ], limit=1)
        subject = '[%s] You have been invited to join the project' \
            % project.name

        if existing_user_id:
            existing_user = nereid_user_obj.browse(existing_user_id[0])
            email_message = render_email(
                text_template='project/emails/inform_addition_2_project_text.html',
                subject=subject, to=email, from_email=CONFIG['smtp_from'],
                project=project, user=existing_user
            )
            self.write(
                project.id, {
                    'participants': [('add', existing_user_id)]
                }
            )
            flash_message = "%s has been invited to the project" \
                % existing_user.display_name

        else:
            invitation_code = ''.join(
                random.sample(string.letters + string.digits, 20)
            )

            new_invite_id = project_invitation_obj.create({
                'email': email,
                'project': project.id,
                'invitation_code': invitation_code
            })
            new_invite = project_invitation_obj.browse(new_invite_id)
            email_message = render_email(
                text_template='project/emails/invite_2_project_text.html',
                subject=subject, to=email, from_email=CONFIG['smtp_from'],
                project=project, invitation=new_invite
            )
            flash_message = "%s has been invited to the project" % email

        server = get_smtp_server()
        server.sendmail(CONFIG['smtp_from'], [email],
            email_message.as_string())
        server.quit()

        if request.is_xhr:
            return jsonify({
                'success': True,
            })
        flash(flash_message)
        return redirect(request.referrer)

    @login_required
    def remove_participant(self, project_id, participant_id):
        """Remove the participant form project
        """
        # Check if user is among the project admins
        if not request.nereid_user.is_project_admin(request.nereid_user):
            flash("Sorry! You are not allowed to remove participants. \
                Contact your project admin for the same.")
            return redirect(request.referrer)

        if request.method == 'POST' and request.is_xhr:
            project = self.get_project(project_id)
            records_to_update = [project.id]
            records_to_update.extend([child.id for child in project.children])
            # If this participant is assigned to any task in this project,
            # that user cannot be removed as tryton's domain does not permit
            # this.
            # So removing assigned user from those tasks as well.
            # TODO: Find a better way to do it, this is memory intensive
            assigned_to_participant = self.search([
                ('id', 'in', records_to_update),
                ('assigned_to', '=', participant_id)
            ])
            self.write(assigned_to_participant, {
                'assigned_to': False,
            })
            self.write(
                records_to_update, {
                    'participants': [('unlink', [participant_id])]
                }
            )

            return jsonify({
                'success': True,
            })

        flash("Could not remove participant! Try again.")
        return redirect(request.referrer)

    @login_required
    def render_task_list(self, project_id):
        """
        Renders a project's task list page
        """
        tag_task_obj = Pool().get('project.work-project.work.tag')
        project = self.get_project(project_id)
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
            filter_domain.append(('name', 'ilike', '%%%s%%' % query))

        tag = request.args.get('tag', None, int)
        if tag:
            filter_domain.append(('tags', '=', tag))

        user = request.args.get('user', None, int)
        if user:
            filter_domain.append(('assigned_to', '=', user))

        counts = {}
        counts['opened_tasks_count'] = self.search(
            filter_domain + [('state', '=', 'opened')], count=True
        )
        counts['done_tasks_count'] = self.search(
            filter_domain + [('state', '=', 'done')], count=True
        )
        counts['all_tasks_count'] = self.search(
            filter_domain, count=True
        )

        if state and state in ('opened', 'done'):
            filter_domain.append(('state', '=', state))
        tasks = Pagination(self, filter_domain, page, 10)
        return render_template(
            'project/task-list.jinja', project=project,
            active_type_name='render_task_list', counts=counts,
            state_filter=state, tasks=tasks
        )

    @login_required
    def render_task(self, task_id, project_id=None):
        """
        Renders the task in a project
        """
        task = self.get_task(task_id)

        comments = sorted(
            task.history + task.timesheet_lines + task.attachments,
            key=lambda x: x.create_date
        )

        timesheet_rows = sorted(
            task.timesheet_lines, key=lambda x: x.employee
        )
        timesheet_summary = groupby(timesheet_rows, key=lambda x: x.employee)

        return render_template(
            'project/task.jinja', task=task, active_type_name='render_task_list',
            project=task.parent, comments=comments,
            timesheet_summary=timesheet_summary
        )

    @login_required
    def render_files(self, project_id):
        project = self.get_project(project_id)
        other_attachments = chain.from_iterable(
            [list(task.attachments) for task in project.children if task.attachments]
        )
        return render_template(
            'project/files.jinja', project=project, active_type_name='files',
            guess_type=guess_type, other_attachments=other_attachments
        )

    @login_required
    def render_timesheet(self, project_id):
        project = self.get_project(project_id)
        return render_template(
            'project/project.jinja', project=project, active_type_name="recent"
        )

    @login_required
    def render_plan(self, project_id):
        """
        Render the plan of the project
        """
        project = self.get_project(project_id)

        if request.is_xhr:
            # XHTTP Request probably from the calendar widget, answer that
            # with json
            start = datetime.fromtimestamp(
                request.args.get('start', type=int)
            )
            end = datetime.fromtimestamp(
                request.args.get('end', type=int)
            )
            # TODO: These times are local times of the user, convert them to
            # UTC (Server time) before using them for comparison
            task_ids = self.search(['AND',
                ('type', '=', 'task'),
                ('parent', '=', project.id),
                ['OR',
                    [
                       ('constraint_start_time', '>=', start),
                    ],
                    [
                        ('constraint_finish_time', '<=', end),
                    ],
                    [
                       ('actual_start_time', '>=', start),
                    ],
                    [
                        ('actual_finish_time', '<=', end),
                    ],
                ]
            ])
            tasks = self.browse(task_ids)
            event_type = request.args['event_type']
            assert event_type in ('constraint', 'actual')

            def to_event(task, type="constraint"):
                event = {
                    'id': task.id,
                    'title': task.name,
                    'url': url_for(
                        'project.work.render_task',
                        project_id=task.parent.id, task_id=task.id),
                }
                event["start"] = getattr(
                    task, '%s_start_time' % type
                ).isoformat()
                if getattr(task, '%s_finish_time' % type):
                    event['end'] = getattr(
                        task, '%s_finish_time' % type
                    ).isoformat()
                return event

            return jsonify(
                result = [
                    # Send all events where there is a start time
                    to_event(task, event_type) for task in tasks \
                        if getattr(task, '%s_start_time' % event_type)
                ]
            )

        return render_template(
            'project/plan.jinja', project=project,
            active_type_name='plan'
        )

    @login_required
    def download_file(self, attachment_id):
        """
        Returns the file for download. The wonership of the task or the
        project is checked automatically.
        """
        attachment_obj = Pool().get('ir.attachment')

        work = None
        if request.args.get('project', None):
            work = self.get_project(request.args.get('project', type=int))
        if request.args.get('task', None):
            work = self.get_task(request.args.get('task', type=int))

        if not work:
            # Neither task, nor the project is specified
            raise abort(404)

        attachment_ids = attachment_obj.search([
            ('id', '=', attachment_id),
            ('resource', '=', '%s,%d' % (self._name, work.id))
        ])
        if not attachment_ids:
            raise abort(404)

        attachment = attachment_obj.browse(attachment_ids[0])
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(attachment.data)

        return send_file(
            f.name, attachment_filename=attachment.name, as_attachment=True
        )

    @login_required
    def upload_file(self):
        """
        Upload the file to a project or task with owner/uploader
        as the current user
        """
        attachment_obj = Pool().get('ir.attachment')

        work = None
        if request.form.get('project', None):
            work = self.get_project(request.form.get('project', type=int))
        if request.form.get('task', None):
            work = self.get_task(request.form.get('task', type=int))

        if not work:
            # Neither task, nor the project is specified
            raise abort(404)

        attached_file =  request.files["file"]

        data = {
            'resource': '%s,%d' % (self._name, work.id),
            'description': request.form.get('description', '')
        }

        if request.form.get('file_type') == 'link':
            link = request.form.get('url')
            data.update({
                'link': link,
                'name': link.split('/')[-1],
                'type': 'link'
            })
        else:
            data.update({
                'data': attached_file.stream.read(),
                'name': attached_file.filename,
                'type': 'data'
            })

        attachment_id = attachment_obj.create(data)

        if request.is_xhr:
            return jsonify({
                'success': True
            })

        flash("Attachment added to %s" % work.name)
        return redirect(request.referrer)

    @login_required
    def update_task(self, task_id, project_id=None):
        """
        Accepts a POST request against a task_id and updates the ticket

        :param task_id: The ID of the task which needs to be updated
        """
        history_obj = Pool().get('project.work.history')

        task = self.get_task(task_id)

        history_data = {
            'project': task.id,
            'updated_by': request.nereid_user.id,
            'comment': request.form['comment']
        }

        updatable_attrs = ['state']
        post_attrs = [request.form.get(attr, None) for attr in updatable_attrs]

        if any(post_attrs):
            # Combined update of task and history since there is some value
            # posted in addition to the comment
            task_changes = {}
            for attr in updatable_attrs:
                if getattr(task, attr) != request.form[attr]:
                    task_changes[attr] = request.form[attr]

            if task_changes:
                # Only write change if anything has really changed
                self.write(task.id, task_changes)
                comment_id = self.browse(task.id).history[-1].id
                history_obj.write(comment_id, history_data)
            else:
                # just create comment since nothing really changed since this
                # update. This is to cover to cover cases where two users who
                # havent refreshed the web page close the ticket
                comment_id = history_obj.create(history_data)
        else:
            # Just comment, no update to task
            comment_id = history_obj.create(history_data)
        history_obj.send_mail(comment_id)

        if request.nereid_user.id not in (p.id for p in task.participants):
            # Add the user to the participants if not already in the list
            self.write(
                task.id, {'participants': [('add', [request.nereid_user.id])]}
            )

        if request.is_xhr:
            comment_record = history_obj.browse(comment_id)
            html = render_template('project/comment.jinja', comment=comment_record)
            return jsonify({
                'success': True,
                'html': html,
                'state': self.browse(task.id).state,
            })
        return redirect(request.referrer)

    @login_required
    def add_tag(self, task_id, tag_id):
        """Assigns the provided to this task

        :param task_id: ID of task
        :param tag_id: ID of tag
        """
        task = self.get_task(task_id)

        self.write(
            task.id, {'tags': [('add', [tag_id])]}
        )

        if request.method == 'POST':
            flash('Tag added to task %s' % task.name)
            return redirect(request.referrer)

        flash("Tag cannot be added")
        return redirect(request.referrer)

    @login_required
    def remove_tag(self, task_id, tag_id):
        """Assigns the provided to this task

        :param task_id: ID of task
        :param tag_id: ID of tag
        """
        task = self.get_task(task_id)

        self.write(
            task.id, {'tags': [('unlink', [tag_id])]}
        )

        if request.method == 'POST':
            flash('Tag removed from task %s' % task.name)
            return redirect(request.referrer)

        flash("Tag cannot be removed")
        return redirect(request.referrer)

    def write(self, ids, values):
        """
        Update write to historize everytime an update is made

        :param ids: ids of the projects
        :param values: A dictionary
        """
        work_history_obj = Pool().get('project.work.history')

        if isinstance(ids, (int, long)):
            ids = [ids]

        for project in self.browse(ids):
            work_history_obj.create_history_line(project, values)

        return super(Project, self).write(ids, values)

    @login_required
    def mark_time(self, task_id):
        """Marks the time against the employee for the task

        :param task_id: ID of task
        """
        timesheet_line_obj = Pool().get('timesheet.line')
        if not request.nereid_user.employee:
            flash("Only employees can mark time on tasks!")
            return redirect(request.referrer)

        task = self.get_task(task_id)

        timesheet_line_obj.create({
            'employee': request.nereid_user.employee.id,
            'hours': request.form['hours'],
            'work': task.id
        })

        flash("Time has been marked on task %s" % task.name)
        return redirect(request.referrer)

    @login_required
    def assign_task(self, task_id):
        """Assign task to a user

        :param task_id: Id of Task
        """
        nereid_user_obj = Pool().get('nereid.user')
        history_obj = Pool().get('project.work.history')

        task = self.get_task(task_id)

        new_assignee = nereid_user_obj.browse(int(request.form['user']))

        if task.assigned_to.id == new_assignee.id:
            flash("Task already assigned to %s" % new_assignee.name)
            return redirect(request.referrer)

        if self.can_write(task.parent, new_assignee):
            self.write(task.id, {
                'assigned_to': new_assignee.id,
                'participants': [('add', [new_assignee.id])]
            })

            comment_id = self.browse(task.id).history[-1].id
            history_obj.send_mail(comment_id)

            if request.is_xhr:
                return jsonify({
                    'success': True,
                })

            flash("Task assigned to %s" % new_assignee.name)
            return redirect(request.referrer)

        flash("Only employees can be assigned to tasks.")
        return redirect(request.referrer)

    @login_required
    def clear_assigned_user(self, task_id):
        """Clear the assigned user from the task

        :param task_id: Id of Task
        """
        task = self.get_task(task_id)

        self.write(task.id, {
            'assigned_to': False
        })

        if request.is_xhr:
            return jsonify({
                'success': True,
            })

        flash("Removed the assigned user from task")
        return redirect(request.referrer)

Project()


class ProjectTag(ModelSQL, ModelView):
    "Tags"
    _name = "project.work.tag"
    _description = __doc__

    name = fields.Char('Name', required=True)
    color = fields.Char('Color Code', required=True)
    project = fields.Many2One(
        'project.work', 'Project', required=True,
        domain=[('type', '=', 'project')], ondelete='CASCADE',
    )

    def __init__(self):
        super(ProjectTag, self).__init__()
        #self._sql_contraints += [
        #    ('unique_name_project', 'UNIQUE(name, project)', 'Duplicate Tag')
        #]

    def default_color(self):
        return "#999"

    @login_required
    def create_tag(self, project_id):
        """Create a new tag for the specific project
        """
        project_obj = Pool().get('project.work')
        project = project_obj.get_project(project_id)
        # Check if user is among the project admins
        if not request.nereid_user.is_project_admin(request.nereid_user):
            flash("Sorry! You are not allowed to create new tags. \
                Contact your project admin for the same.")
            return redirect(request.referrer)

        if request.method == 'POST':
            tag_id = self.create({
                'name': request.form['name'],
                'color': request.form['color'],
                'project': project_id
            })

            flash("Successfully created tag")
            return redirect(request.referrer)

        flash("Could not create tag. Try Again")
        return redirect(request.referrer)

    @login_required
    def delete_tag(self, tag_id):
        """Delete the tag from project
        """
        # Check if user is among the project admins
        if not request.nereid_user.is_project_admin(request.nereid_user):
            flash("Sorry! You are not allowed to delete tags. \
                Contact your project admin for the same.")
            return redirect(request.referrer)

        if request.method == 'POST' and request.is_xhr:
            tag_id = self.delete(tag_id)

            return jsonify({
                'success': True,
            })

        flash("Could not delete tag! Try again.")
        return redirect(request.referrer)

ProjectTag()


class TaskTags(ModelSQL):
    _name = 'project.work-project.work.tag'
    _table = 'project_work_tag_rel'

    task = fields.Many2One(
        'project.work', 'Project',
        ondelete='CASCADE', select=1, required=True,
        domain=[('type', '=', 'task')]
    )

    tag = fields.Many2One(
        'project.work.tag', 'Tag', select=1, required=True, ondelete='CASCADE',
    )

TaskTags()


class ProjectHistory(ModelSQL, ModelView):
    'Project Work History'
    _name = 'project.work.history'
    _description = __doc__

    date = fields.DateTime('Change Date')
    create_uid = fields.Many2One('res.user', 'Create User')

    #: The reverse many to one for history field to work
    project = fields.Many2One('project.work', 'Project Work')

    # Nereid user who made this update
    updated_by = fields.Many2One('nereid.user', 'Updated By')


    # States
    previous_state = fields.Selection([
        ('opened', 'Opened'),
        ('done', 'Done'),
        ], 'Prev. State', select=True)
    new_state = fields.Selection([
        ('opened', 'Opened'),
        ('done', 'Done'),
        ], 'New State', select=True)

    # Comment
    comment = fields.Text('Comment')

    # Name
    previous_name = fields.Char('Prev. Name')
    new_name = fields.Char('New Name')

    # Assigned to
    previous_assigned_to = fields.Many2One('nereid.user', 'Prev. Assignee')
    new_assigned_to = fields.Many2One('nereid.user', 'New Assignee')

    # other fields
    previous_constraint_start_time = fields.DateTime("Constraint Start Time")
    new_constraint_start_time = fields.DateTime("Next Constraint Start Time")

    previous_constraint_finish_time = fields.DateTime("Constraint  Finish Time")
    new_constraint_finish_time = fields.DateTime("Constraint  Finish Time")

    def default_date(self):
        return datetime.utcnow()

    def create_history_line(self, project, changed_values):
        """
        Creates a history line from the changed values of a project.work
        """
        if changed_values:
            data = {}

            # TODO: Also create a line when assigned user is cleared from task
            for field in ('assigned_to', 'state',
                    'constraint_start_time', 'constraint_finish_time'):
                if field not in changed_values or not changed_values[field]:
                    continue
                data['previous_%s' % field] = getattr(project, field)
                data['new_%s' % field] = changed_values[field]

            if data:
                if has_request_context():
                    data['updated_by'] = request.nereid_user.id
                else:
                    # TODO: try to find the nereid user from the employee
                    # if an employee made the update
                    pass
                data['project'] = project.id
                return self.create(data)

    def get_function_fields(self, ids, names):
        """
        Function to compute fields

        :param ids: the ids of works
        :param names: the list of field name to compute
        :return: a dictionary with all field names as key and
                 a dictionary as value with id as key
        """
        pass

    def set_function_fields(self, ids, name, value):
        pass

    @login_required
    def update_comment(self, task_id, comment_id):
        """
        Update a specific comment.
        """
        project_obj = Pool().get('project.work')
        nereid_user_obj = Pool().get('nereid.user')

        # allow modification only if the user is an admin or the author of
        # this ticket
        task = project_obj.browse(task_id)
        comment = self.browse(comment_id)
        assert task.type == "task"
        assert comment.project.id == task.id

        # Allow only admins and author of this comment to edit it
        if nereid_user_obj.is_project_admin(request.nereid_user) or \
                comment.updated_by == request.nereid_user:
            self.write(comment_id, {'comment': request.form['comment']})
        else:
            abort(403)

        if request.is_xhr:
            comment_record = self.browse(comment_id)
            html = render_template('project/comment.jinja', comment=comment_record)
            return jsonify({
                'success': True,
                'html': html,
                'state': project_obj.browse(task.id).state,
            })
        return redirect(request.referrer)

    def send_mail(self, history_id):
        """Send mail to all participants whenever there is any update on
        project.

        :param history_id: ID of history.
        """
        history = self.browse(history_id)

        # Get the previous updates than the latest one.
        history_ids = self.search([
            ('id', '<', history_id),
            ('project.id', '=', history.project.id)
        ], order=[('create_date', 'DESC')])

        last_history = self.browse(history_ids)

        # Prepare the content of email.
        subject = "[%s] %s" % (
            history.project.parent.name, history.project.work.name,
        )

        receivers = [s.email for s in history.project.participants
                     if s.email]

        if not receivers:
            return

        message = render_email(
            from_email=CONFIG['smtp_from'],
            to=', '.join(receivers),
            subject=subject,
            text_template='project/emails/text_content.jinja',
            html_template='project/emails/html_content.jinja',
            history=history,
            last_history=last_history
        )

        #message.add_header('reply-to', request.nereid_user.email)

        # Send mail.
        server = get_smtp_server()
        server.sendmail(CONFIG['smtp_from'], receivers,
            message.as_string())
        server.quit()

ProjectHistory()


@registration.connect
def invitation_new_user_handler(nereid_user_id):
    """When the invite is sent to a new user, he is sent an invitation key
    with the url which guides the user to registration page

        This method checks if the invitation key is present in the url
        If yes, search for the invitation with this key, attache the user
            to the invitation and project to the user
        If not, perform normal operation
    """
    try:
        invitation_obj = Pool().get('project.work.invitation')
        project_obj = Pool().get('project.work')
    except KeyError:
        # Just return silently. This KeyError is cause if the module is not
        # installed for a specific database but exists in the python path
        # and is loaded by the tryton module loader
        warnings.warn(
            "nereid-project module installed but not in database",
            DeprecationWarning, stacklevel=2
        )
        return

    invitation_code = request.args.get('invitation_code')
    if not invitation_code:
        return
    ids = invitation_obj.search([
        ('invitation_code', '=', invitation_code)
    ])

    if not ids:
        return

    invitation = invitation_obj.browse(ids[0])
    invitation_obj.write(invitation.id, {
        'nereid_user': nereid_user_id
    })

    project_obj.write(
        invitation.project.id, {
            'participants': [('add', [nereid_user_id])]
        }
    )
    invitation_obj.delete(invitation.id)
