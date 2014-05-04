# -*- coding: utf-8 -*-
"""
    company

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.pool import PoolMeta
from trytond.model import ModelSQL, fields

__all__ = ['Company', 'CompanyProjectAdmins']
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
