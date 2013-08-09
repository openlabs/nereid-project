# -*- coding: utf-8 -*-
'''
    nereid_project

    :copyright: (c) 2010-2013 by Openlabs Technologies & Consulting (P) Ltd.
    :license: GPLv3, see LICENSE for more details

'''
from trytond.pool import Pool

from project import (
    WebSite, ProjectUsers, ProjectInvitation,
    ProjectWorkInvitation, TimesheetEmployeeDay, Project, Tag,
    TaskTags, ProjectHistory, ProjectWorkCommit, Activity,
)
from company import Company, CompanyProjectAdmins, NereidUser


def register():
    """This function will register trytond module project_billing
    """
    Pool.register(
        WebSite,
        ProjectUsers,
        ProjectInvitation,
        ProjectWorkInvitation,
        TimesheetEmployeeDay,
        Project,
        Tag,
        TaskTags,
        ProjectHistory,
        ProjectWorkCommit,
        Activity,
        Company,
        CompanyProjectAdmins,
        NereidUser,
        module='nereid_project', type_='model',
    )
