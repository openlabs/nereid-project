# -*- coding: utf-8 -*-
"""
    Configuration

    :copyright: (c) 2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import os
import base64
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton


__all__ = ['Configuration']


class Configuration(ModelSingleton, ModelSQL, ModelView):
    "Project Configuration"
    __name__ = 'project.configuration'

    git_webhook_secret = fields.Char('GitHub Webhook Secret', required=True)

    @staticmethod
    def default_git_webhook_secret():
        return base64.urlsafe_b64encode(os.urandom(30))
