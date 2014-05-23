# -*- coding: utf-8 -*-
"""
    activity

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.model import fields
from trytond.pool import PoolMeta
from nereid import request

__all__ = ['Activity']
__metaclass__ = PoolMeta


class Activity:
    '''
    Nereid user activity
    '''
    __name__ = "nereid.activity"

    project = fields.Many2One(
        'project.work', 'Project', domain=[('type', '=', 'project')]
    )

    @classmethod
    def get_activity_stream_domain(cls):
        '''
        Returns the domain to get activity stream of project where current user
        is participant
        '''
        return [
            'OR', [
                ('project.members.user', '=', request.nereid_user.id),
            ], [
                ('project.participants', '=', request.nereid_user.id)
            ], [
                ('actor', '=', request.nereid_user.id)
            ]
        ]
