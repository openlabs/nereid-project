#!/usr/bin/env python
import os
import datetime
import mimetypes

from nereid import Nereid
from werkzeug.contrib.sessions import FilesystemSessionStore
from nereid.contrib.locale import Babel
from nereid.sessions import Session
from raven.contrib.flask import Sentry

CWD = os.path.abspath(os.path.dirname(__file__))
DATABASE_NAME = os.environ.get('TRYTOND_DB_NAME', 'nereid_project')
SECRET_PATH = os.environ.get('SECRET_PATH', '.secret')

from trytond.config import CONFIG
CONFIG.update_etc()


APP_CONFIG = dict(

    # The name of database
    DATABASE_NAME=DATABASE_NAME,

    # If the application is to be configured in the debug mode
    DEBUG=False,

    # The location where the translations of this template are stored
    TRANSLATIONS_PATH='i18n',

    SECRET_KEY=open(SECRET_PATH).read(),

)
# Create a new application
app = Nereid(static_folder='%s/static/' % CWD, static_url_path='/static')

# Update the configuration with the above config values
app.config.update(APP_CONFIG)

# Initialise the app, connect to cache and backend
app.initialise()
app.jinja_env.filters[
    'float_to_time'] = lambda hours: "%dh %dm" % (hours, (hours * 60) % 60)
app.jinja_env.globals.update({
    'datetime': datetime,
    'guess_mimetype': mimetypes.guess_type,
})

# Setup the filesystem cache for session store.
# This wont work if you scale on more than one servers.
# Use something like redissessionstore or memcached store
app.session_interface.session_store = FilesystemSessionStore(
    '/tmp', session_class=Session
)

Babel(app)
sentry = Sentry(app)


if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0')
