# -*- coding: utf-8 -*-
"""
    website

    :copyright: (c) 2012-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.pool import PoolMeta
from nereid import route, login_required, redirect, url_for

__all__ = ['WebSite']
__metaclass__ = PoolMeta


class WebSite:
    """
    Website
    """
    __name__ = "nereid.website"

    @classmethod
    @route('/')
    @login_required
    def home(cls):
        """
        Put recent projects into the home
        """
        return redirect(url_for('project.work.home'))
