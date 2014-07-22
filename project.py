# -*- coding: utf-8 -*-
"""
    project

    Extend the project to allow users

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import os
import uuid
import re
import tempfile
import time
import dateutil.parser
import calendar
from collections import defaultdict
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from itertools import chain, cycle
from mimetypes import guess_type
from email.utils import parseaddr

import simplejson as json
from babel.dates import parse_date, format_date
from nereid import (
    request, abort, render_template, login_required, url_for, redirect,
    flash, jsonify, render_email, permissions_required, current_app, route,
    current_user
)
from flask import send_file
from flask.helpers import send_from_directory
from nereid.ctx import has_request_context
from nereid.contrib.pagination import Pagination
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval
from trytond.config import CONFIG
from trytond import backend

from utils import request_wants_json
import hashlib
import hmac

__all__ = [
    'ProjectWorkMember', 'ProjectInvitation',
    'ProjectWorkInvitation', 'Project', 'ProjectHistory', 'ProjectWorkCommit',
]
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

#: Get the static folder. The static folder also
#: goes into the site packages
STATIC_FOLDER = os.path.join(
    os.path.abspath(
        os.path.dirname(__file__)
    ), 'static'
)


class ProjectWorkMember(ModelSQL, ModelView):
    "Project Work Member"
    __name__ = 'project.work.member'

    user = fields.Many2One(
        "nereid.user", "Nereid User", required=True, select=True
    )
    role = fields.Selection([
        ('admin', 'Admin'),
        ('member', 'Member'),
    ], "Role", required=True)
    project = fields.Many2One(
        "project.work", "Project", required=True, select=True
    )

    @classmethod
    def __setup__(cls):
        super(ProjectWorkMember, cls).__setup__()
        cls._sql_constraints += [(
            'check_user',
            'UNIQUE(project, "user")',
            'Users must be unique per project'
        )]

    @staticmethod
    def default_role():
        """
        Sets default role
        """
        return 'member'

    @classmethod
    def __register__(cls, module_name):
        '''
        Register class and migrate data from old table(project_work-nereid_user)
        to new table (project_work_user) only for porject participants
        '''
        cursor = Transaction().cursor
        TableHandler = backend.get('TableHandler')

        table_exist = TableHandler.table_exist(cursor, 'project_work_member')

        super(ProjectWorkMember, cls).__register__(module_name)

        if not table_exist:
            ProjectUsers = Pool().get('project.work-nereid.user')
            ProjectWork = Pool().get('project.work')
            company_user = Pool().get('company.company-nereid.user')

            # Migrate project participants from old user table to new member
            # table
            cursor.execute(
                "INSERT INTO %s (project, \"user\", role) "
                "SELECT old.task, old.user, 'member' from \"%s\" old "
                "JOIN %s as p on old.task=p.id where p.type='project'"
                % (
                    cls._table, ProjectUsers._table, ProjectWork._table
                )
            )

            cursor.execute("SELECT id from project_work where type='project'")
            for project in cursor.fetchall():

                # Add project admins as admin member of all projects
                cursor.execute(
                    "INSERT INTO %s (project, \"user\", role) "
                    "SELECT %d, a.user, 'admin' from \"%s\" a "
                    "WHERE NOT EXISTS "
                    "(select * from %s b where b.user=a.user and b.project=%d)"
                    % (
                        cls._table, project[0], company_user._table, cls._table,
                        project[0]
                    )
                )

            # If project admin is already member of project update the role as
            # admin
            cursor.execute(
                "UPDATE \"%s\""
                "SET role='admin' "
                "WHERE \"user\" IN (select b.user from %s b) "
                % (
                    cls._table, company_user._table
                )
            )


class ProjectInvitation(ModelSQL, ModelView):
    "Project Invitation store"
    __name__ = 'project.work.invitation'

    email = fields.Char('Email', required=True, select=True)
    invitation_code = fields.Char(
        'Invitation Code', select=True
    )
    nereid_user = fields.Many2One('nereid.user', 'Nereid User')
    project = fields.Many2One('project.work', 'Project')

    joining_date = fields.Function(
        fields.DateTime('Joining Date', depends=['nereid_user']),
        'get_joining_date'
    )

    @classmethod
    def __setup__(cls):
        super(ProjectInvitation, cls).__setup__()
        cls._sql_constraints += [
            (
                'invitation_code_unique',
                'UNIQUE(invitation_code)',
                'Invitation code cannot be same',
            ),
        ]

    @staticmethod
    def default_invitation_code():
        """
        Sets the default invitation code as uuid everytime
        """
        return unicode(uuid.uuid4())

    def get_joining_date(self, name):
        """
        Joining Date of User
        """
        if self.nereid_user:
            return self.nereid_user.create_date

    @login_required
    @route('/invitation-<int:active_id>/-remove', methods=['GET', 'POST'])
    def remove_invite(self):
        """
        Remove the invite to a participant from project
        """
        # Check if user is among the project admins
        if not request.nereid_user.is_admin_of_project(self.project):
            flash(
                "Sorry! You are not allowed to remove invited users." +
                " Contact your project admin for the same."
            )
            return redirect(request.referrer)

        if request.method == 'POST':
            self.delete([self])

            if request.is_xhr:
                return jsonify({
                    'success': True,
                })

            flash(
                "Invitation to the user has been voided."
                "The user can no longer join the project unless reinvited"
            )
        return redirect(request.referrer)

    @login_required
    @route('/invitation-<int:active_id>/-resend', methods=['GET', 'POST'])
    def resend_invite(self):
        """Resend the invite to a participant
        """
        EmailQueue = Pool().get('email.queue')

        # Check if user is among the project admin members
        if not request.nereid_user.is_admin_of_project(self.project):
            flash(
                "Sorry! You are not allowed to resend invites. "
                "Contact your project admin for the same."
            )
            return redirect(request.referrer)

        if request.method == 'POST':
            subject = '[%s] You have been re-invited to join the project' \
                % self.project.rec_name
            email_message = render_email(
                text_template='project/emails/invite_2_project_text.html',
                subject=subject, to=self.email,
                from_email=CONFIG['smtp_from'], project=self.project,
                invitation=self
            )
            EmailQueue.queue_mail(
                CONFIG['smtp_from'], self.email,
                email_message.as_string()
            )

            if request.is_xhr:
                return jsonify({
                    'success': True,
                })

            flash("Invitation has been resent to %s." % self.email)
        return redirect(request.referrer)


class ProjectWorkInvitation(ModelSQL):
    "Project Work Invitation"
    __name__ = 'project.work-project.invitation'

    invitation = fields.Many2One(
        'project.work.invitation', 'Invitation',
        ondelete='CASCADE', select=1, required=True
    )
    project = fields.Many2One(
        'project.work.invitation', 'Project',
        ondelete='CASCADE', select=1, required=True
    )


class Project:
    """
    Tryton itself is very flexible in allowing multiple layers of Projects and
    sub projects. But having this and implementing this seems to be too
    convulted for everyday use. So nereid simplifies the process to:

    - Project::Associated to a party
       |
       |-- Task (Type is task)
    """
    __name__ = 'project.work'

    history = fields.One2Many(
        'project.work.history', 'project',
        'History', readonly=True
    )
    members = fields.One2Many(
        'project.work.member', 'project', 'Members',
        states={'invisible': Eval('type') != 'project'},
        depends=['type']
    )

    admins = fields.Function(
        fields.One2Many('nereid.user', None, "Admins"), 'get_admins'
    )

    tags_for_projects = fields.One2Many(
        'project.work.tag', 'project', 'Tags',
        states={
            'invisible': Eval('type') != 'project',
            'readonly': Eval('type') != 'project',
        }
    )

    created_by = fields.Many2One('nereid.user', 'Created by')

    #: Get all the attachments on the object and return them
    attachments = fields.Function(
        fields.One2Many('ir.attachment', None, 'Attachments'),
        'get_attachments'
    )

    repo_commits = fields.One2Many(
        'project.work.commit', 'project', 'Repo Commits'
    )

    @staticmethod
    def default_created_by():
        if has_request_context() and not current_user.is_anonymous():
            return current_user.id
        return None

    def get_admins(self, name):
        """
        Return all admin users of the project
        """

        assert self.type == 'project'

        return [
            member.user.id for member in self.members
            if member.role == 'admin'
        ]

    @classmethod
    @route('/projects')
    @login_required
    def home(cls):
        """
        Put recent projects into the home
        """
        domain = [
            ('type', '=', 'project'),
            ('parent', '=', None),
        ]

        if not request.nereid_user.has_permissions(['project.admin']):
            # If not project admin, then the project only where user has
            # a membership is shown
            domain.append(('members.user', '=', request.nereid_user.id))

        projects = sorted(cls.search(domain), key=lambda p: p.rec_name)

        if request.is_xhr:
            return jsonify({
                'itemCount': len(projects),
                'items': map(lambda project: project.serialize(), projects),
            })
        return render_template('project/home.jinja', projects=projects)

    def serialize(self, purpose=None):
        """
        Serialize a record, which could be a task or project

        """
        assigned_to = None
        if self.assigned_to:
            assigned_to = self.assigned_to.serialize('listing')

        value = {
            'id': self.id,
            'name': self.rec_name,
            'type': self.type,
            'parent': self.parent and self.parent.id or None,
            # Task specific
            'tags': map(lambda t: t.name, self.tags),
            'assigned_to': assigned_to,
            'attachments': len(self.attachments),
            'progress_state': self.progress_state,
            'comment': self.comment,
            'create_date': self.create_date.isoformat(),
            'constraint_finish_time': (
                self.constraint_finish_time and
                self.constraint_finish_time.isoformat() or None
            )
        }

        if self.type == 'task':
            # Computing the effort for project is expensive
            value['hours'] = self.hours
            value['effort'] = self.effort
            value['total_effort'] = self.total_effort
            value['project'] = self and self.id
            value['created_by'] = self.created_by and \
                self.created_by.serialize('listing')
        elif purpose == 'activity_stream':
            value['create_date'] = self.create_date.isoformat()
            value['id'] = self.id
            value['displayName'] = self.rec_name
            value['type'] = self.type
            value['objectType'] = self.__name__
        elif self.type == 'project':
            value['url'] = url_for(
                'project.work.render_project', project_id=self.id
            )
        else:
            value['all_participants'] = [
                participant.serialize('listing') for participant in
                self.all_participants
            ]
            # TODO: Convert self.parent to self.project
            value['url'] = url_for(
                'project.work.render_task', project_id=self.parent.id,
                task_id=self.id,
            )
        return value

    @classmethod
    @route('/rst-to-html', methods=['GET', 'POST'])
    def rst_to_html(cls):
        """
        Return the response as rst converted to html
        """
        text = request.form['text']
        return render_template('project/rst_to_html.jinja', text=text)

    def get_attachments(self, name):
        """
        Return all the attachments in the object
        """
        Attachment = Pool().get('ir.attachment')

        return map(
            int, Attachment.search([
                ('resource', '=', '%s,%d' % (self.__name__, self.id))
            ])
        )

    def can_read(self, user, silent=False):
        """
        Returns true if the given nereid user can read the project

        :param user: The browse record of the current nereid user
        """
        if user.has_permissions(['project.admin']):
            return True
        if user not in map(lambda member: member.user, self.members):
            if silent:
                return False
            raise abort(404)
        return True

    def can_write(self, user, silent=False):
        """
        Returns true if the given user can write to the project

        :param user: The browse record of the current nereid user
        """
        if user.has_permissions(['project.admin']):
            return True
        if user not in map(lambda member: member.user, self.members):
            if silent:
                return False
            raise abort(404)
        return True

    @classmethod
    def get_project(cls, project_id):
        """
        Common base for fetching the project while validating if the user
        can use it.

        :param project_id: Project Id of project to fetch.
        """
        projects = cls.search([
            ('id', '=', project_id),
            ('type', '=', 'project'),
        ])

        if not projects:
            raise abort(404)

        if not projects[0].can_read(request.nereid_user, silent=True):
            # If the user is not allowed to access this project then dont let
            raise abort(404)

        return projects[0]

    @classmethod
    @route('/project-<int:project_id>')
    @login_required
    def render_project(cls, project_id):
        """
        Renders a project

        :param project_id: Project Id of project to render.
        """
        # TODO: Convert to instance method
        project = cls.get_project(project_id)
        if request.is_xhr:
            rv = project.serialize()
            rv['participants'] = [
                member.user.serialize('listing') for member in project.members
            ]
            return jsonify(rv)
        return render_template(
            'project/project.jinja', project=project, active_type_name="recent"
        )

    @classmethod
    @route('/project/-new', methods=['GET', 'POST'])
    @login_required
    @permissions_required(['project.admin'])
    def create_project(cls):
        """Create a new project

        POST will create a new project
        """
        Activity = Pool().get('nereid.activity')
        Work = Pool().get('timesheet.work')

        if request.method == 'POST':
            project, = cls.create([{
                'work': Work.create([{
                    'name': request.form['name'],
                    'company': request.nereid_website.company.id,
                }])[0].id,
                'type': 'project',
                'members': [
                    ('create', [{
                        'user': request.nereid_user.id,
                        'role': 'admin',
                    }])
                ]
            }])
            Activity.create([{
                'actor': request.nereid_user.id,
                'object_': 'project.work, %d' % project.id,
                'verb': 'created_project',
                'project': project.id,
            }])
            flash("Project successfully created.")
            return redirect(
                url_for('project.work.render_project', project_id=project.id)
            )

        flash("Could not create project. Try again.")
        return redirect(request.referrer)

    @classmethod
    @route('/project-<int:project_id>/-permissions')
    @login_required
    def permissions(cls, project_id):
        """
        Permissions for the project

        :params project_id: project's id to check permission
        """
        ProjectInvitation = Pool().get('project.work.invitation')

        project = cls.get_project(project_id)

        if not request.nereid_user.is_admin_of_project(project):
            abort(404)

        invitations = ProjectInvitation.search([
            ('project', '=', project.id),
            ('nereid_user', '=', None)
        ])
        return render_template(
            'project/permissions.jinja', project=project,
            invitations=invitations, active_type_name='permissions'
        )

    @classmethod
    @login_required
    def projects_list(cls, page=1):
        """
        Render a list of projects
        """
        projects = cls.search([
            ('party', '=', request.nereid_user.party),
        ])
        return render_template('project/projects.jinja', projects=projects)

    @classmethod
    @route('/project-<int:project_id>/-invite', methods=['POST'])
    @login_required
    def invite(cls, project_id):
        """Invite a user via email to the project

        :param project_id: ID of Project
        """
        NereidUser = Pool().get('nereid.user')
        ProjectInvitation = Pool().get('project.work.invitation')
        Activity = Pool().get('nereid.activity')
        EmailQueue = Pool().get('email.queue')

        project = cls.get_project(project_id)

        if not request.nereid_user.is_admin_of_project(project):
            flash(
                "You are not allowed to invite users for this project"
            )
            return redirect(request.referrer)

        if not request.method == 'POST':
            return abort(404)

        email = request.form['email']

        existing_user = NereidUser.search([
            ('email', '=', email),
            ('company', '=', request.nereid_website.company.id),
        ], limit=1)

        subject = '[%s] You have been invited to join the project' \
            % project.rec_name
        if existing_user:
            # If participant already existed
            if existing_user[0] in [m.user for m in project.members]:
                flash("%s has been already added as a participant \
                    for the project" % existing_user[0].display_name)
                return redirect(request.referrer)

            email_message = render_email(
                text_template="project/emails/"
                "inform_addition_2_project_text.html",
                subject=subject, to=email, from_email=CONFIG['smtp_from'],
                project=project, user=existing_user[0]
            )
            cls.write(
                [project], {
                    'members': [
                        ('create', [{'user': existing_user[0].id}])
                    ]
                }
            )
            Activity.create([{
                'actor': existing_user[0].id,
                'object_': 'project.work, %d' % project.id,
                'verb': 'joined_project',
                'project': project.id,
            }])
            flash_message = "%s has been invited to the project" \
                % existing_user[0].display_name

        else:
            new_invite, = ProjectInvitation.create([{
                'email': email,
                'project': project.id,
            }])
            email_message = render_email(
                text_template='project/emails/invite_2_project_text.html',
                subject=subject, to=email, from_email=CONFIG['smtp_from'],
                project=project, invitation=new_invite
            )
            flash_message = "%s has been invited to the project" % email

        EmailQueue.queue_mail(
            CONFIG['smtp_from'], email,
            email_message.as_string()
        )

        if request.is_xhr:
            return jsonify({
                'success': True,
            })
        flash(flash_message)
        return redirect(request.referrer)

    @login_required
    @route(
        '/project-<int:active_id>/participant-<int:participant_id>/-remove',
        methods=['GET', 'POST']
    )
    def remove_participant(self, participant_id):
        """
        Remove the participant from the project
        """
        Activity = Pool().get('nereid.activity')
        ProjectMember = Pool().get('project.work.member')

        # Check if user is admin member of the project
        if not request.nereid_user.is_admin_of_project(self):
            flash(
                "Sorry! You are not allowed to remove participants." +
                " Contact your project admin for the same."
            )
            return redirect(request.referrer)

        task_ids_to_update = []

        if request.method == 'POST' and request.is_xhr:
            task_ids_to_update.extend([child.id for child in self.children])
            # If this participant is assigned to any task in this project,
            # that user cannot be removed as tryton's domain does not permit
            # this.
            # So removing assigned user from those tasks as well.
            # TODO: Find a better way to do it, this is memory intensive
            assigned_to_participant = self.search([
                ('id', 'in', task_ids_to_update),
                ('assigned_to', '=', participant_id)
            ])
            self.write(assigned_to_participant, {
                'assigned_to': None,
            })
            self.write(
                map(
                    lambda rec_id: self.__class__(rec_id),
                    task_ids_to_update
                ), {'participants': [('unlink', [participant_id])]}
            )

            project_member, = ProjectMember.search([
                ('project', '=', self.id),
                ('user', '=', participant_id),
            ])
            self.write([self], {
                'members': [('delete', [project_member.id])]
            })

            # FIXME: I think object_ in activity should be
            # project.work-nereid.user models record.
            object_ = 'nereid.user, %d' % participant_id

            Activity.create([{
                'actor': request.nereid_user.id,
                'object_': object_,
                'target': 'project.work, %d' % self.id,
                'verb': 'removed_participant',
                'project': self.id,
            }])

            return jsonify({
                'success': True,
            })

        flash("Could not remove participant! Try again.")
        return redirect(request.referrer)

    @classmethod
    @route('/project-<int:project_id>/-files', methods=['GET', 'POST'])
    @login_required
    def render_files(cls, project_id):
        project = cls.get_project(project_id)
        other_attachments = chain.from_iterable(
            [list(task.attachments) for task in project.children if
                task.attachments]
        )
        return render_template(
            'project/files.jinja', project=project,
            active_type_name='files', guess_type=guess_type,
            other_attachments=other_attachments
        )

    @classmethod
    def _get_expected_date_range(cls):
        """Return the start and end date based on the GET arguments.
        Also asjust for the full calendar asking for more information than
        it actually must show

        The last argument of the tuple returns a boolean to show if the
        weekly table/aggregation should be displayed
        """
        start = datetime.fromtimestamp(
            request.args.get('start', type=int)
        ).date()
        end = datetime.fromtimestamp(
            request.args.get('end', type=int)
        ).date()
        if (end - start).days < 20:
            # this is not a month call, just some smaller range
            return start, end
        # This is a data call for a month, but fullcalendar tries to
        # fill all the days in the first and last week from the prev
        # and next month. So just return start and end date of the month
        mid_date = start + relativedelta(days=((end - start).days / 2))
        ignore, last_day = calendar.monthrange(mid_date.year, mid_date.month)
        return (
            date(year=mid_date.year, month=mid_date.month, day=1),
            date(year=mid_date.year, month=mid_date.month, day=last_day),
        )

    @classmethod
    def get_week(cls, day):
        """
        Return the week for any given day
        """
        if (day >= 1) and (day <= 7):
            return '01-07'
        elif (day >= 8) and (day <= 14):
            return '08-14'
        elif (day >= 15) and (day <= 21):
            return '15-21'
        else:
            return '22-END'

    @classmethod
    def get_task_from_work(cls, work):
        '''
        Returns task from work

        :param work: Instance of work
        '''
        with Transaction().set_context(active_test=False):
            task, = cls.search([('work', '=', work.id)], limit=1)
            return task

    @classmethod
    def get_calendar_data(cls, project=None):
        """
        Returns the calendar data
        """
        Timesheet = Pool().get('timesheet.line')
        ProjectWork = Pool().get('project.work')
        Employee = Pool().get('company.employee')

        if request.args.get('timesheet_lines_of'):
            # This request only expects timesheet lines and the request comes
            # in the format date:employee_id:project_id
            date, employee_id, project_id = request.args.get(
                'timesheet_lines_of').split(':')
            domain = [
                ('date', '=', datetime.strptime(date, '%Y-%m-%d').date()),
                ('employee', '=', int(employee_id))
            ]
            if int(project_id):
                project = ProjectWork(int(project_id))
                domain.append(('work.parent', 'child_of', [project.work.id]))
            lines = Timesheet.search(
                domain, order=[('date', 'asc'), ('employee', 'asc')]
            )
            return jsonify(lines=[
                unicode(render_template(
                    'project/timesheet-line.jinja', line=line,
                    related_task=cls.get_task_from_work(line.work)
                ))
                for line in lines[::-1]
            ])

        start, end = cls._get_expected_date_range()

        day_totals = []
        color_map = {}
        colors = cycle([
            'grey', 'RoyalBlue', 'CornflowerBlue', 'DarkSeaGreen',
            'SeaGreen', 'Silver', 'MediumOrchid', 'Olive',
            'maroon', 'PaleTurquoise'
        ])
        query = '''SELECT
                timesheet_line.employee,
                timesheet_line.date,
        '''

        if project:
            query += 'project_work.id AS project,'
        else:
            query += '0 AS project,'
        query += '''SUM(timesheet_line.hours) AS sum
            FROM timesheet_line
            JOIN timesheet_work ON timesheet_work.id = timesheet_line.work \
            AND timesheet_work.parent IS NOT NULL
            JOIN project_work ON project_work.work = timesheet_work.parent
            WHERE
                timesheet_line.date >= %s AND
                timesheet_line.date <= %s
        '''
        qargs = [start, end]
        if project:
            qargs.append(project.id)
            query += 'AND project_work.id = %s'

        if request.args.get('employee', None) and \
                request.nereid_user.has_permissions(['project.admin']):
                qargs.append(request.args.get('employee', None, int))
                query += 'AND timesheet_line.employee = %s'

        query += '''
            GROUP BY
                timesheet_line.employee,
                timesheet_line.date
        '''
        if project:
            query += ',project_work.id'

        Transaction().cursor.execute(query, qargs)
        raw_data = Transaction().cursor.fetchall()

        hours_by_week_employee = defaultdict(lambda: defaultdict(float))
        for employee_id, date, project_id, hours in raw_data:
            employee = Employee(employee_id)
            day_totals.append({
                'id': '%s:%s:%s' % (date, employee.id, project_id),
                'title': '%s (%dh %dm)' % (
                    employee.rec_name, hours, (hours * 60) % 60
                ),
                'start': date.isoformat(),
                'color': color_map.setdefault(employee, colors.next()),
            })
            hours_by_week_employee[cls.get_week(date.day)][employee] += hours

        total_by_employee = defaultdict(float)
        for employee_hours in hours_by_week_employee.values():
            for employee, hours in employee_hours.iteritems():
                total_by_employee[employee] += hours

        work_week = render_template(
            'project/work-week.jinja', data_by_week=hours_by_week_employee,
            total_by_employee=total_by_employee
        )
        return jsonify(
            day_totals=day_totals, lines=[],
            work_week=unicode(work_week)
        )

    @classmethod
    @route('/-project/-my-last-7-days')
    @login_required
    def get_7_day_performance(cls):
        """
        Returns the hours worked in the last 7 days.
        """
        Timesheet = Pool().get('timesheet.line')
        Date_ = Pool().get('ir.date')

        if not request.nereid_user.employee:
            return jsonify({})

        end_date = Date_.today()
        start_date = end_date - relativedelta(days=7)

        timesheet_lines = Timesheet.search([
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('employee', '=', request.nereid_user.employee.id),
        ])

        hours_by_day = {}

        for line in timesheet_lines:
            hours_by_day[line.date] = \
                hours_by_day.setdefault(line.date, 0.0) + line.hours

        days = hours_by_day.keys()
        days.sort()

        return jsonify({
            'categories': map(lambda d: d.strftime('%d-%b'), days),
            'series': ['%.2f' % hours_by_day[day] for day in days]
        })

    @classmethod
    def get_comparison_data(cls):
        """
        Compare the performance of people
        """
        Date = Pool().get('ir.date')
        Employee = Pool().get('company.employee')

        employee_ids = request.args.getlist('employee', type=int)
        if not employee_ids:
            employees = Employee.search([])
            employee_ids = map(lambda emp: emp.id, employees)
        else:
            employees = Employee.browse(employee_ids)

        employees = dict(zip(employee_ids, employees))

        end_date = Date.today()
        if request.args.get('end_date'):
            end_date = parse_date(
                request.args['end_date'],
                locale='en_IN',
                # locale=Transaction().context.get('language')
            )
        start_date = end_date - relativedelta(months=1)
        if request.args.get('start_date'):
            start_date = parse_date(
                request.args['start_date'],
                locale='en_IN',
                # locale=Transaction().context.get('language')
            )

        if start_date > end_date:
            flash('Invalid date Range')
            return redirect(request.referrer)

        Transaction().cursor.execute(
            'SELECT * FROM timesheet_by_employee_by_day '
            'WHERE "date" >= %s '
            'AND "date" <= %s '
            'AND "employee" in %s '
            'ORDER BY "date"',
            (start_date, end_date, tuple(employee_ids))
        )
        raw_data = Transaction().cursor.fetchall()
        categories = map(
            lambda d: start_date + relativedelta(days=d),
            range(0, (end_date - start_date).days + 1)
        )
        hours_by_date_by_employee = {}
        for employee_id, line_date, hours in raw_data:
            hours_by_date_by_employee.setdefault(
                line_date, {})[employee_id] = hours
        series = []
        for employee_id in employee_ids:
            employee = employees.get(employee_id)
            series.append({
                'name': employee and employee.rec_name or 'Ghost',
                'type': 'column',
                'data': map(
                    lambda d:
                        hours_by_date_by_employee.get(d, {})
                        .get(employee_id, 0), categories
                )
            })

        additional = [{
            'type': 'pie',
            'name': 'Total Hours',
            'data': map(
                lambda d: {'name': d['name'], 'y': sum(d['data'])}, series
            ),
            'center': [40, 40],
            'size': 100,
            'showInLegend': False,
            'dataLabels': {
                'enabled': False
            }
        }]
        additional.extend([{
            'type': 'line',
            'name': '{0} Avg'.format(serie['name']),
            'data': (
                [sum(serie['data']) / len(serie['data'])] * len(categories),
            )
        } for serie in series])

        return jsonify(
            categories=map(lambda d: d.strftime('%d-%b'), categories),
            series=series + additional
        )

    @classmethod
    @login_required
    @permissions_required(perm_any=['project.admin', 'project.manager'])
    def get_gantt_data(cls):
        """
        Get gantt data for the last 1 month.
        """
        Date = Pool().get('ir.date')
        Employee = Pool().get('company.employee')

        employees = Employee.search([])
        employee_ids = map(lambda emp: emp.id, employees)
        employees = dict(zip(employee_ids, employees))

        today = Date.today()
        start_date = today - relativedelta(months=2)

        Transaction().cursor.execute(
            'SELECT * FROM timesheet_by_employee_by_day '
            'WHERE "date" >= \'%s\'' % (start_date, )
        )
        raw_data = Transaction().cursor.fetchall()
        employee_wise_data = {}
        get_class = lambda h: (h < 4) and 'ganttRed' or \
            (h < 6) and 'ganttOrange' or 'ganttGreen'
        for employee_id, line_date, hours in raw_data:
            value = {
                'from': line_date - relativedelta(days=1),
                # Gantt has a bug of 1 day off
                'to': line_date - relativedelta(days=1),
                'label': '%.1f' % hours,
                'customClass': get_class(hours)
            }
            employee_wise_data.setdefault(employee_id, []).append(value)

        gantt_data = []
        gantt_data_append = gantt_data.append
        for employee_id, values in employee_wise_data.iteritems():
            employee = employees.get(employee_id)
            gantt_data_append({
                'name': employee and employee.rec_name or 'Ghost',
                'desc': '',
                'values': values,
            })
        gantt_data = sorted(gantt_data, key=lambda item: item['name'].lower())
        date_handler = lambda o: \
            '/Date(%d)/' % (time.mktime(o.timetuple()) * 1000) \
            if hasattr(o, 'timetuple') else o
        return json.dumps(gantt_data, default=date_handler)

    @classmethod
    @route('/projects/-compare-performance')
    @login_required
    @permissions_required(perm_any=['project.admin', 'project.manager'])
    def compare_performance(cls):
        """
        Compare the performance of people
        """
        Employee = Pool().get('company.employee')
        Date = Pool().get('ir.date')

        if request.is_xhr:
            return cls.get_comparison_data()
        employees = Employee.search([])
        today = Date.today()
        return render_template(
            'project/compare-performance.jinja', employees=employees,
            start_date=today - relativedelta(days=7),
            end_date=today
        )

    @classmethod
    @route('/projects/-gantt')
    @login_required
    @permissions_required(perm_any=['project.admin', 'project.manager'])
    def render_global_gantt(cls):
        """
        Renders a global gantt
        """
        Employee = Pool().get('company.employee')

        if request.is_xhr:
            return cls.get_gantt_data()
        employees = Employee.search([])
        return render_template(
            'project/global-gantt.jinja', employees=employees
        )

    @classmethod
    @route('/projects/timesheet')
    @login_required
    @permissions_required(perm_any=['project.admin', 'project.manager'])
    def render_global_timesheet(cls):
        '''
        Returns rendered timesheet template.
        '''
        Employee = Pool().get('company.employee')

        if request.is_xhr:
            return cls.get_calendar_data()
        employees = Employee.search([])
        return render_template(
            'project/global-timesheet.jinja', employees=employees
        )

    @classmethod
    @route('/project-<int:project_id>/-timesheet')
    @login_required
    def render_timesheet(cls, project_id):
        '''
        Returns rendered timesheet template.
        '''
        project = cls.get_project(project_id)
        employees = [
            p.employee for p in project.all_participants if p.employee
        ]
        if request.is_xhr:
            return cls.get_calendar_data(project)
        return render_template(
            'project/timesheet.jinja', project=project,
            active_type_name="timesheet", employees=employees
        )

    @classmethod
    @route('/project-<int:project_id>/-plan')
    @login_required
    def render_plan(cls, project_id):
        """
        Render the plan of the project
        """
        project = cls.get_project(project_id)
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
            tasks = cls.search([
                'AND',
                ('type', '=', 'task'),
                ('parent', '=', project.id), [
                    'OR', [
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
            event_type = request.args['event_type']
            assert event_type in ('constraint', 'actual')

            def to_event(task, type="constraint"):
                event = {
                    'id': task.id,
                    'title': task.rec_name,
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
                result=[
                    # Send all events where there is a start time
                    to_event(task, event_type) for task in tasks
                        if getattr(task, '%s_start_time' % event_type)
                ]
            )

        return render_template(
            'project/plan.jinja', project=project,
            active_type_name='plan'
        )

    @classmethod
    @route('/attachment-<int:attachment_id>/-download')
    @login_required
    def download_file(cls, attachment_id):
        """
        Returns the file for download. The ownership of the task or the
        project is checked automatically.
        """
        Attachment = Pool().get('ir.attachment')

        work = None
        if request.args.get('project', None):
            work = cls.get_project(request.args.get('project', type=int))
        if request.args.get('task', None):
            work = cls.get_task(request.args.get('task', type=int))

        if not work:
            # Neither task, nor the project is specified
            raise abort(404)

        attachment, = Attachment.search([
            ('id', '=', attachment_id),
            ('resource', '=', '%s,%d' % (cls.__name__, work.id))
        ], limit=1)

        if attachment.type == 'link':
            return redirect(attachment.link)

        if not attachment:
            raise abort(404)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(attachment.data)

        return send_file(
            f.name, attachment_filename=attachment.name, as_attachment=True
        )

    @classmethod
    @route('/attachment/-upload', methods=['GET', 'POST'])
    @login_required
    def upload_file(cls):
        """
        Upload the file to a project or task with owner/uploader
        as the current user
        """
        work = None
        if request.form.get('project', None):
            work = cls.get_project(request.form.get('project', type=int))
        if request.form.get('task', None):
            work = cls.get_task(request.form.get('task', type=int))

        if not work:
            # Neither task, nor the project is specified
            raise abort(404)

        # Create attachment
        if request.form.get('file_type') == 'link':
            link = request.form.get('url')
            attachment = work.create_attachment(
                link.split('/')[-1], data=link, type='link'
            )
        else:
            file = request.files["file"]
            attachment = work.create_attachment(
                file.filename, data=file.stream.read()
            )

        if request.is_xhr or request_wants_json():
            with Transaction().set_context(task=work.id):
                return jsonify({
                    'data': attachment.serialize('listing'),
                }), 201

        flash("Attachment added to %s" % work.rec_name)
        return redirect(request.referrer)

    def create_attachment(self, filename, data, type='data'):
        """
        Creates attchment for project

        :param filename: Name of the file
        :param data: Content of the file or Url of the file
        :param type: Either data or link
        """
        Attachment = Pool().get('ir.attachment')

        assert type in ('data', 'link')

        resource = '%s,%d' % (self.__name__, self.id)

        if Attachment.search([
            ('name', '=', filename),
            ('resource', '=', resource)
        ]):
            # Try to create a unique filename
            filename, extension = filename.split('.', 1)
            filename = '%s-%d.%s' % (
                filename, time.time(), extension
            )
        values = {
            'data': data,
            'name': filename,
            'type': type,
            'resource': resource,
        }

        if has_request_context():
            values.update({
                'description': request.form.get('description', '')
            })

        return Attachment.create([values])[0]

    @classmethod
    def write(cls, projects, values):
        """
        Update write to historize everytime an update is made

        :param projects: List of active records of projects
        :param values: A dictionary
        """
        WorkHistory = Pool().get('project.work.history')

        for project in projects:
            WorkHistory.create_history_line(project, values)

        return super(Project, cls).write(projects, values)

    @login_required
    @route('/project-<int:active_id>/stream')
    def stream(self):
        '''
        Return stream for a project.
        '''
        Activity = Pool().get('nereid.activity')

        self.can_read(request.nereid_user)
        page = request.args.get('page', 1, int)

        domain = [('project', '=', self.id)]
        activities = Pagination(
            Activity, domain, page, request.args.get('limit', 20, type=int)
        )
        items = filter(
            None, map(lambda activity: activity.serialize(), activities)
        )
        return jsonify({
            'totalItems': activities.count,
            'items': items,
        })

    @classmethod
    @route('/project/stats')
    @login_required
    def stats(cls):
        """
        Return a JSOn of the performance of employees
        """
        Date = Pool().get('ir.date')

        if not request.nereid_user.employee:
            raise abort(403)

        cursor = Transaction().cursor
        query = """
            SELECT
                count(timesheet_line.id) AS c,
                party.name AS name,
                sum(hours) AS hours
            FROM timesheet_line
            JOIN company_employee ON company_employee.id=timesheet_line.employee
            JOIN party_party AS party ON party.id=company_employee.party
            WHERE timesheet_line.date >= %s AND timesheet_line.date <= %s
            GROUP BY party.name ORDER BY sum(hours) DESC;
        """
        end_date = Date.today()
        if request.args.get('end_date'):
            end_date = parse_date(
                request.args['end_date'],
                locale='en_IN',
            )
        start_date = end_date - relativedelta(months=1)
        if request.args.get('start_date'):
            start_date = parse_date(
                request.args['start_date'],
                locale='en_IN',
            )
        cursor.execute(query, (start_date, end_date))
        top_time_reporters = cursor.fetchall()

        query = """
            SELECT count(project_work_history.id) AS c, party.name AS name
            FROM project_work_history
            JOIN nereid_user ON nereid_user.id = project_work_history.updated_by
            JOIN party_party AS party ON party.id = nereid_user.party
            WHERE
                project_work_history.create_date >= %s
                AND project_work_history.create_date <= %s
                AND nereid_user.employee IS NOT NULL
            GROUP BY party.name ORDER BY count(project_work_history.id) DESC;
        """
        cursor.execute(query, (start_date, end_date))
        top_commentors = cursor.fetchall()

        return jsonify(
            start_date=format_date(start_date, locale='en_IN'),
            end_date=format_date(end_date, locale='en_IN'),
            top_time_reporters=top_time_reporters,
            top_commentors=top_commentors,
        )

    @classmethod
    @route('/static-project/<path:filename>')
    def send_static_file(self, filename):
        """Function used internally to send static files from the static
        folder to the browser.
        """
        cache_timeout = current_app.get_send_file_max_age(filename)
        return send_from_directory(
            STATIC_FOLDER, filename,
            cache_timeout=cache_timeout
        )

    @classmethod
    def verify_github_payload_sign(cls, payload, signature, secret):
        """
        Returns True if the webhook signature matches the
        computed signature
        """
        computed_signature = "sha1=%s" % (
            hmac.HMAC(str(secret), payload, hashlib.sha1).hexdigest(),
        )

        return (computed_signature == signature)


class ProjectHistory(ModelSQL, ModelView):
    'Project Work History'
    __name__ = 'project.work.history'

    date = fields.DateTime('Change Date')  # date is python built
    create_uid = fields.Many2One('res.user', 'Create User')

    #: The reverse many to one for history field to work
    project = fields.Many2One('project.work', 'Project Work')

    # Nereid user who made this update
    updated_by = fields.Many2One('nereid.user', 'Updated By')
    # States
    previous_state = fields.Selection([
        (None, ''),
        ('opened', 'Opened'),
        ('done', 'Done'),
    ], 'Prev. State', select=True
    )
    new_state = fields.Selection([
        (None, ''),
        ('opened', 'Opened'),
        ('done', 'Done'),
    ], 'New State', select=True
    )
    previous_progress_state = fields.Selection(
        PROGRESS_STATES, 'Prev. Progress State', select=True
    )
    new_progress_state = fields.Selection(
        PROGRESS_STATES, 'New Progress State', select=True
    )

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

    previous_constraint_finish_time = fields.DateTime("Constraint Finish Time")
    new_constraint_finish_time = fields.DateTime("Constraint  Finish Time")

    comment_markup = fields.Selection([
        (None, 'Plain Text'),
        ('rst', 'reStructuredText'),
        ('markdown', 'Markdown'),
    ], 'Comment Markup Type')

    @staticmethod
    def default_date():
        '''
        Return current datetime in utcformat as default for date.
        '''
        return datetime.utcnow()

    def serialize(self, purpose=None):
        '''
        Serialize the history and returns a dictionary.
        '''
        return {
            "create_date": self.create_date.isoformat(),
            "url": url_for(
                'project.work.render_task', project_id=self.project.parent.id,
                task_id=self.project.id,
            ),
            'updatedBy': self.updated_by.serialize('listing'),
            "objectType": self.__name__,
            "id": self.id,
            "displayName": self.rec_name,
            "comment": self.comment,
            "new_state": self.new_state,
            "new_progress_state": self.new_progress_state,
            "previous_progress_state": self.previous_progress_state,
            "new_assignee": (
                self.new_assigned_to.serialize('listing')
                if self.new_assigned_to
                    else None
            )
        }

    @classmethod
    def create_history_line(cls, project, changed_values):
        """
        Creates a history line from the changed values of a project.work
        """
        if changed_values:
            data = {}

            # TODO: Also create a line when assigned user is cleared from task
            for field in (
                'assigned_to', 'state', 'progress_state',
                'constraint_start_time', 'constraint_finish_time'
            ):
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
                return cls.create([data])

    @login_required
    @route(
        '/task-<int:task_id>/comment-<int:active_id>/-update',
        methods=['GET', 'POST']
    )
    def update_comment(self, task_id):
        """
        Update a specific comment.
        """
        Project = Pool().get('project.work')

        # allow modification only if the user is an admin or the author of
        # this ticket
        task = Project(task_id)
        assert task.type == "task"
        assert self.project.id == task.id

        # Allow only admins and author of this comment to edit it
        if request.nereid_user.is_admin_of_project(task.parent) or \
                self.updated_by == request.nereid_user:
            self.write([self], {'comment': request.form['comment']})
        else:
            abort(403)

        if request.is_xhr:
            html = render_template('project/comment.jinja', comment=self)
            return jsonify({
                'success': True,
                'html': unicode(html),
                'state': task.state,
            })
        return redirect(request.referrer)

    def send_mail(self):
        """
        Send mail to all participants whenever there is any update on
        project.

        """
        EmailQueue = Pool().get('email.queue')

        # Get the previous updates than the latest one.
        last_history = self.search([
            ('id', '<', self.id),
            ('project.id', '=', self.project.id)
        ], order=[('create_date', 'DESC')])

        # Prepare the content of email.
        subject = "[#%s %s] - %s" % (
            self.project.id, self.project.parent.rec_name,
            self.project.work.name,
        )

        receivers = map(
            lambda member: member.user.email,
            filter(lambda member: member.user.email, self.project.members)
        )

        if self.updated_by.email in receivers:
            receivers.remove(self.updated_by.email)

        if not receivers:
            return

        message = render_email(
            from_email=CONFIG['smtp_from'],
            to=', '.join(receivers),
            subject=subject,
            text_template='project/emails/text_content.jinja',
            html_template='project/emails/html_content.jinja',
            history=self,
            last_history=last_history
        )

        # message.add_header('reply-to', request.nereid_user.email)

        # Send mail.
        EmailQueue.queue_mail(
            CONFIG['smtp_from'], receivers,
            message.as_string()
        )

    @staticmethod
    def default_comment_markup():
        return 'rst'


class ProjectWorkCommit(ModelSQL, ModelView):
    "Repository commits"
    __name__ = 'project.work.commit'
    _rec_name = 'commit_message'

    commit_timestamp = fields.DateTime('Commit Timestamp')
    project = fields.Many2One(
        'project.work', 'Project', required=True, select=True
    )
    nereid_user = fields.Many2One(
        'nereid.user', 'User', required=True, select=True
    )
    repository = fields.Char('Repository Name', required=True, select=True)
    repository_url = fields.Char('Repository URL', required=True)
    commit_message = fields.Char('Commit Message', required=True)
    commit_url = fields.Char('Commit URL', required=True)
    commit_id = fields.Char('Commit Id', required=True)

    @classmethod
    @route('/-project/-github-hook', methods=['POST'])
    def commit_github_hook_handler(cls):
        """
        Handle post commit posts from GitHub
        See https://help.github.com/articles/post-receive-hooks
        """
        NereidUser = Pool().get('nereid.user')
        Activity = Pool().get('nereid.activity')
        Project = Pool().get('project.work')
        Configuration = Pool().get('project.configuration')

        if request.method == "POST":
            payload = json.loads(request.get_data())

            # Exit if Headers has no signature
            if 'X-Hub-Signature' not in request.headers:
                raise Exception(
                    "Github Commit Hook: Headers has no signature"
                )

            # Exit if signature does not begin with 'sha1='
            if not request.headers['X-Hub-Signature'].startswith('sha1='):
                raise Exception(
                    "Github Commit Hook: signature does not begin with 'sha1='"
                )
            if not Project.verify_github_payload_sign(
                request.get_data() + request.headers.get("Date", ""),
                request.headers['X-Hub-Signature'],
                Configuration(1).git_webhook_secret
            ):
                raise Exception(
                    "Github Commit Hook: Payload signature is invalid"
                )

            for commit in payload['commits']:
                nereid_users = NereidUser.search([
                    ('email', '=', commit['author']['email'])
                ])
                if not nereid_users:
                    continue

                projects = set([
                    int(x) for x in re.findall(
                        r'#(\d+)', commit['message']
                    )
                ])
                pull_requests = set([
                    int(x) for x in re.findall(
                        r'pull request #(\d+)', commit['message']
                    )
                ])
                for project in Project.browse(projects - pull_requests):
                    local_commit_time = dateutil.parser.parse(
                        commit['timestamp']
                    )
                    commit_timestamp = local_commit_time.astimezone(
                        dateutil.tz.tzutc()
                    )
                    commit_hook = cls.search([
                        ('commit_id', '=', commit['id']),
                        ('project', '=', project),
                    ])
                    if commit_hook:
                        continue
                    work_commit, = cls.create([{
                        'commit_timestamp': commit_timestamp,
                        'project': project,
                        'nereid_user': nereid_users[0].id,
                        'repository': payload['repository']['name'],
                        'repository_url': payload['repository']['url'],
                        'commit_message': commit['message'],
                        'commit_url': commit['url'],
                        'commit_id': commit['id']
                    }])
                    Activity.create([{
                        'actor': nereid_users[0].id,
                        'object_': 'project.work.commit, %d' % work_commit.id,
                        'verb': 'made_commit',
                        'target': 'project.work, %d' % project.id,
                        'project': project.parent.id,
                    }])
        return 'OK'

    def serialize(self, purpose=None):
        return {
            'create_date': self.create_date.isoformat(),
            "objectType": self.__name__,
            "id": self.id,
            "updatedBy": self.nereid_user.serialize('listing'),
            "url": self.commit_url,
            "displayName": self.commit_message,
            "repository": self.repository,
            "repository_url": self.repository_url,
            "commit_timestamp": self.commit_timestamp.isoformat(),
            "commit_id": self.commit_id,
        }

    @classmethod
    @route('/-project/-bitbucket-hook', methods=['GET', 'POST'])
    def commit_bitbucket_hook_handler(cls):
        """
        Handle post commit posts from bitbucket
        See below
        https://confluence.atlassian.com/display/BITBUCKET/
        POST+Service+Management
        """
        NereidUser = Pool().get('nereid.user')

        if request.method == "POST":
            payload = json.loads(request.form['payload'])
            for commit in payload['commits']:
                nereid_users = NereidUser.search([
                    ('email', '=', parseaddr(commit['raw_author'])[1])
                ])
                if not nereid_users:
                    continue

                projects = set([
                    int(x) for x in re.findall(
                        r'#(\d+)', commit['message']
                    )
                ])
                pull_requests = set([
                    int(x) for x in re.findall(
                        r'pull request #(\d+)', commit['message']
                    )
                ])
                for project in projects - pull_requests:
                    local_commit_time = dateutil.parser.parse(
                        commit['utctimestamp']
                    )
                    commit_timestamp = local_commit_time.astimezone(
                        dateutil.tz.tzutc()
                    )
                    cls.create([{
                        'commit_timestamp': commit_timestamp,
                        'project': project,
                        'nereid_user': nereid_users[0].id,
                        'repository': payload['repository']['name'],
                        'repository_url': (
                            payload['canon_url'] +
                            payload['repository']['absolute_url']
                        ),
                        'commit_message': commit['message'],
                        'commit_url': (
                            payload['canon_url'] +
                            payload['repository']['absolute_url'] +
                            "changeset/" +
                            commit['raw_node']
                        ),
                        'commit_id': commit['raw_node']
                    }])
        return 'OK'
