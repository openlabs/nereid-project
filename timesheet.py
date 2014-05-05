# -*- coding: utf-8 -*-
"""
    timesheet

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from nereid import url_for
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.config import CONFIG

__all__ = ['TimesheetEmployeeDay', 'TimesheetLine']
__metaclass__ = PoolMeta


class TimesheetEmployeeDay(ModelView):
    'Gantt dat view generator'
    __name__ = 'timesheet_by_employee_by_day'

    employee = fields.Many2One('company.employee', 'Employee')
    date = fields.Date('Date')
    hours = fields.Float('Hours', digits=(16, 2))

    @classmethod
    def __register__(cls, module_name):
        """
        Init Method

        :param module_name: Name of the module
        """
        super(TimesheetEmployeeDay, cls).__register__(module_name)

        query = '"timesheet_by_employee_by_day" AS ' \
                'SELECT timesheet_line.employee, timesheet_line.date, ' \
                'SUM(timesheet_line.hours) AS sum ' \
                'FROM "timesheet_line" ' \
                'GROUP BY timesheet_line.date, timesheet_line.employee;'

        if CONFIG['db_type'] == 'postgres':
            Transaction().cursor.execute('CREATE OR REPLACE VIEW ' + query)

        elif CONFIG['db_type'] == 'sqlite':
            Transaction().cursor.execute('CREATE VIEW IF NOT EXISTS ' + query)


class TimesheetLine:
    '''
    Timesheet Lines
    '''
    __name__ = 'timesheet.line'

    def serialize(self, purpose=None):
        '''
        Serialize timesheet line and returns a dictionary.
        '''
        nereid_user_obj = Pool().get('nereid.user')

        try:
            nereid_user, = nereid_user_obj.search([
                ('employee', '=', self.employee.id)
            ], limit=1)
        except ValueError:
            nereid_user = {}
        else:
            nereid_user = nereid_user.serialize('listing')

        # Render url for timesheet line is task on which this time is marked
        return {
            'create_date': self.create_date.isoformat(),
            "url": url_for(
                'project.work.render_task', project_id=self.work.parent.id,
                task_id=self.work.id,
            ),
            "objectType": self.__name__,
            "id": self.id,
            "displayName": "%dh %dm" % (self.hours, (self.hours * 60) % 60),
            "updatedBy": nereid_user,
        }
