# -*- coding: utf-8 -*-
"""
    company

    Add the employee relation ship to nereid user

    :copyright: (c) 2012 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from nereid import request
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


NereidUser()
