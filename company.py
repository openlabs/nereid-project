# -*- coding: utf-8 -*-
"""
    company

    Add the employee relation ship to nereid user

    :copyright: (c) 2012-2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from datetime import datetime

from nereid import request, jsonify, login_required
from trytond.pool import Pool, PoolMeta
from trytond.model import ModelSQL, fields

__all__ = ['Company', 'CompanyProjectAdmins', 'NereidUser']
__metaclass__ = PoolMeta


class Company:
    """
    Add project admins to company
    """
    __name__ = "company.company"

    #: Administrators for project management.Only admins can create new
    #: project.
    project_admins = fields.Many2Many(
        'company.company-nereid.user', 'company', 'user',
        'Project Administrators'
    )


class CompanyProjectAdmins(ModelSQL):
    "Company Admins"
    __name__ = 'company.company-nereid.user'
    _table = 'company_company_nereid_user_rel'

    company = fields.Many2One(
        'company.company', 'Company',
        ondelete='CASCADE', select=1, required=True)

    user = fields.Many2One(
        'nereid.user', 'User', select=1, required=True
    )


class NereidUser:
    """
    Add employee
    """
    __name__ = "nereid.user"

    #: Allow the nereid user to be connected to an internal employee. This
    #: indicates that the user is an employee and not a regular participant
    employee = fields.Many2One('company.employee', 'Employee', select=True)

    def _json(self):
        '''
        Serialize NereidUser and return a dictonary.
        '''
        result = super(NereidUser, self)._json()
        result['image'] = {
            'url': self.get_profile_picture(size=20),
        }
        result['email'] = self.email
        result['employee'] = self.employee and self.employee.id or None
        result['permissions'] = [p.value for p in self.permissions]
        return result

    @classmethod
    @login_required
    def profile(cls):
        """
        User profile
        """
        if request.method == "GET" and request.is_xhr:
            user, = cls.browse([request.nereid_user.id])
            return jsonify(user._json())
        return super(NereidUser, cls).profile()

    def is_project_admin(self):
        """
        Returns True if the user is in the website admins list

        :return: True or False
        """
        if self in request.nereid_website.company.project_admins:
            return True
        return False

    def hours_reported_today(self):
        """
        Returns the number of hours the nereid_user has done on the
        current date.

        """
        Timesheet = Pool().get('timesheet.line')

        if not self.employee:
            return 0.00

        current_date = datetime.utcnow().date()
        lines = Timesheet.search([
            ('date', '=', current_date),
            ('employee', '=', self.employee.id),
        ])

        return sum(map(lambda line: line.hours, lines))
