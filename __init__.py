# -*- coding: utf-8 -*-
'''
    nereid_project

    :copyright: (c) 2010-2013 by Openlabs Technologies & Consulting (P) Ltd.
    :license: GPLv3, see LICENSE for more details

'''
from trytond.pool import Pool

from project import (
    WebSite, ProjectUsers, ProjectInvitation,
    TimesheetEmployeeDay, ProjectWorkInvitation, Project, Tag,
    TaskTags, ProjectHistory, ProjectWorkCommit, TimesheetLine, Activity,
    Attachment,
)
from company import Company, CompanyProjectAdmins, NereidUser


def register():
    """This function will register trytond module nereid_project
    """
    Pool.register(
        WebSite,
        ProjectUsers,
        ProjectInvitation,
        TimesheetEmployeeDay,
        ProjectWorkInvitation,
        Project,
        Tag,
        TaskTags,
        ProjectHistory,
        ProjectWorkCommit,
        TimesheetLine,
        Activity,
        Company,
        CompanyProjectAdmins,
        NereidUser,
        Attachment,
        module='nereid_project', type_='model',
    )
