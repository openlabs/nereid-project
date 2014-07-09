# -*- coding: utf-8 -*-
"""
    company

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.pool import PoolMeta, Pool
from trytond.model import ModelSQL, fields

__all__ = ['Company', 'CompanyProjectAdmins']
__metaclass__ = PoolMeta


class Company:
    """
    Add project admins to company
    """
    __name__ = "company.company"

    project_admins = fields.Function(
        fields.One2Many("nereid.user", None, "Project Admins"),
        'get_admins'
    )

    project_managers = fields.Function(
        fields.One2Many("nereid.user", None, "Project Managers"),
        'get_admins'
    )

    def get_admins(self, name):
        """
        Returns all the nereid users who are admin for this company
        """
        NereidUser = Pool().get('nereid.user')

        assert name in ('project_admins', 'project_managers')

        if name == 'project_admins':
            permission = 'project.admin'
        else:
            permission = 'project.manager'

        domain = [
            ('company', '=', self.id),
            ('permissions.value', '=', permission),
        ]

        return map(int, NereidUser.search(domain))


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
