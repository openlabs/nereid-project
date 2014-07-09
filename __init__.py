# -*- coding: utf-8 -*-
'''
    nereid_project

    :copyright: (c) 2010-2014 by Openlabs Technologies & Consulting (P) Ltd.
    :license: GPLv3, see LICENSE for more details

'''
from trytond.pool import Pool

from website import WebSite
from project import (
    ProjectWorkMember, ProjectInvitation, ProjectWorkInvitation,
    Project, ProjectHistory, ProjectWorkCommit
)
from activity import Activity
from attachment import Attachment
from timesheet import TimesheetEmployeeDay, TimesheetLine
from tag import Tag, TaskTags
from company import Company, CompanyProjectAdmins
from user import NereidUser
from configuration import Configuration
from task import TaskUsers, Task


def register():
    """This function will register trytond module nereid_project
    """
    Pool.register(
        WebSite,
        Company,
        CompanyProjectAdmins,
        TaskUsers,
        ProjectWorkMember,
        ProjectInvitation,
        TimesheetEmployeeDay,
        ProjectWorkInvitation,
        Project,
        Tag,
        TaskTags,
        ProjectHistory,
        ProjectWorkCommit,
        Task,
        TimesheetLine,
        Activity,
        NereidUser,
        Attachment,
        Configuration,
        module='nereid_project', type_='model',
    )
