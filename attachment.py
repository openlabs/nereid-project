# -*- coding: utf-8 -*-
"""
    attachment

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.transaction import Transaction
from trytond.model import fields
from trytond.pool import PoolMeta
from nereid import request, url_for
from nereid.ctx import has_request_context

__all__ = ['Attachment']
__metaclass__ = PoolMeta


class Attachment:
    '''
    Ir Attachment
    '''
    __name__ = "ir.attachment"

    active = fields.Boolean("Active")
    uploaded_by = fields.Many2One("nereid.user", "Uploaded By")

    @staticmethod
    def default_uploaded_by():
        """
        Sets current nereid user as default for uploaded_by
        """
        if has_request_context():
            return request.nereid_user.id

    @staticmethod
    def default_active():
        """
        Sets default for active
        """
        return True

    def serialize(self, purpose=None):
        rv = {
            'create_date': self.create_date.isoformat(),
            "objectType": self.__name__,
            "id": self.id,
            "updatedBy": self.uploaded_by.serialize('listing'),
            "displayName": self.name,
            "description": self.description,
        }
        if has_request_context():
            rv['downloadUrl'] = url_for(
                'project.work.download_file',
                attachment_id=self.id,
                task=Transaction().context.get('task'),
            )
        return rv
