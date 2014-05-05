# -*- coding: utf-8 -*-
"""
    tag

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from nereid import (
    request, login_required, url_for, redirect,
    flash, jsonify, route
)
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend

__all__ = ['Tag', 'TaskTags']
__metaclass__ = PoolMeta


class Tag(ModelSQL, ModelView):
    "Tags"
    __name__ = "project.work.tag"

    name = fields.Char('Name', required=True)
    color = fields.Char('Color Code', required=True)
    project = fields.Many2One(
        'project.work', 'Project', required=True,
        domain=[('type', '=', 'project')], ondelete='CASCADE',
    )

    @classmethod
    def __setup__(cls):
        super(Tag, cls).__setup__()
        cls._sql_constraints += [
            ('unique_name_project', 'UNIQUE(name, project)', 'Duplicate Tag')
        ]

    @staticmethod
    def default_color():
        '''
        Default for color
        '''
        return "#999"

    def serialize(self, purpose=None):
        '''
        Serialize the tag and returns a dictionary.
        '''
        return {
            'create_date': self.create_date.isoformat(),
            "url": url_for(
                'project.work.render_task_list', project_id=self.project.id,
                state="opened", tag=self.id
            ),
            "objectType": self.__name__,
            "id": self.id,
            "displayName": self.name,
        }

    @classmethod
    @route('/project-<int:project_id>/tag/-new', methods=['GET', 'POST'])
    @login_required
    def create_tag(cls, project_id):
        """
        Create a new tag for the specific project

        :params project_id: Project id for which need to be created
        """
        Project = Pool().get('project.work')
        Activity = Pool().get('nereid.activity')

        project = Project.get_project(project_id)

        # Check if user is among the project admins
        if not request.nereid_user.is_project_admin():
            flash(
                "Sorry! You are not allowed to create new tags." +
                " Contact your project admin for the same."
            )
            return redirect(request.referrer)

        if request.method == 'POST':
            tag, = cls.create([{
                'name': request.form['name'],
                'color': request.form['color'],
                'project': project.id
            }])
            Activity.create([{
                'actor': request.nereid_user.id,
                'object_': 'project.work.tag, %d' % tag.id,
                'verb': 'created_tag',
                'target': 'project.work, %d' % project.id,
                'project': project.id,
            }])

            flash("Successfully created tag")
            return redirect(request.referrer)

        flash("Could not create tag. Try Again")
        return redirect(request.referrer)

    @login_required
    @route('/tag-<int:active_id>/-delete', methods=['GET', 'POST'])
    def delete_tag(self):
        """
        Delete the tag from project
        """
        # Check if user is among the project admins
        if not request.nereid_user.is_project_admin():
            flash(
                "Sorry! You are not allowed to delete tags." +
                " Contact your project admin for the same."
            )
            return redirect(request.referrer)

        if request.method == 'POST' and request.is_xhr:
            self.delete([self])

            return jsonify({
                'success': True,
            })

        flash("Could not delete tag! Try again.")
        return redirect(request.referrer)


class TaskTags(ModelSQL):
    'Task Tags'
    __name__ = 'project.work-project.work.tag'

    task = fields.Many2One(
        'project.work', 'Project',
        ondelete='CASCADE', select=1, required=True,
        domain=[('type', '=', 'task')]
    )

    tag = fields.Many2One(
        'project.work.tag', 'Tag', select=1, required=True, ondelete='CASCADE',
    )

    @classmethod
    def __register__(cls, module_name):
        '''
        Register class and update table name to new.
        '''
        cursor = Transaction().cursor
        TableHandler = backend.get('TableHandler')
        table = TableHandler(cursor, cls, module_name)
        super(TaskTags, cls).__register__(module_name)

        # Migration
        if table.table_exist(cursor, 'project_work_tag_rel'):
            table.table_rename(
                cursor, 'project_work_tag_rel', 'project_work-project_work_tag'
            )
