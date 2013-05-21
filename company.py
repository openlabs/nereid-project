# -*- coding: utf-8 -*-
"""
    company

    Add the employee relation ship to nereid user

    :copyright: (c) 2012-2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from datetime import datetime

from nereid import request
from trytond.pool import Pool, PoolMeta
from trytond.model import ModelSQL, fields

__all__ = ['Company', 'CompanyProjectAdmins', 'NereidUser']
__metaclass__ = PoolMeta


class Company:
    """
    Add project admins to company
    """
    __name__ = "company.company"

    #: Administrators for project management. Only admins can create new 
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
    employee = fields.Many2One('company.employee', 'Employee',
        select=True,
    )

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
