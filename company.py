# -*- coding: utf-8 -*-
"""
    company

    Add the employee relation ship to nereid user

    :copyright: (c) 2012-2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from datetime import datetime

from nereid import request
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Get


class Company(ModelSQL, ModelView):
    """
    Add project admins to company
    """
    _name = "company.company"

    #: Administrators for project management. Only admins can create new 
    project_admins = fields.Many2Many(
        'company.company-nereid.user', 'company', 'user',
        'Project Administrators'
    )

Company()


class CompanyProjectAdmins(ModelSQL):
    _name = 'company.company-nereid.user'
    _table = 'company_company_nereid_user_rel'

    company = fields.Many2One(
        'company.company', 'Company',
        ondelete='CASCADE', select=1, required=True)

    user = fields.Many2One(
        'nereid.user', 'User', select=1, required=True
    )

CompanyProjectAdmins()


class NereidUser(ModelSQL, ModelView):
    """
    Add employee
    """
    _name = "nereid.user"

    #: Allow the nereid user to be connected to an internal employee. This
    #: indicates that the user is an employee and not a regular participant
    employee = fields.Many2One('company.employee', 'Employee',
        select=True, domain=[
            ('company', '=', Get(Eval('context', {}), 'company')),
            ('party', '=', Eval('party'))
    ])

    def is_project_admin(self, user):
        """
        Returns True if the user is in the website admins list

        :param user: Browse record of the user
        :return: True
        """
        if user in request.nereid_website.company.project_admins:
            return True
        return False

    def hours_reported_today(self, user):
        """
        Returns the number of hours the nereid_user has done on the
        current date.

        :param user: Browse record of the nereid user
        """
        timesheet_obj = Pool().get('timesheet.line')

        if not user.employee:
            return 0.00


        current_date = datetime.utcnow().date()
        line_ids = timesheet_obj.search([
            ('date', '=', current_date),
            ('employee', '=', user.employee.id),
        ])
        lines = timesheet_obj.browse(line_ids)

        return sum(map(lambda line: line.hours, lines))

NereidUser()
