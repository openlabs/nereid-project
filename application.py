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


def float_to_time(hours):
    "Converts a float of hours into readable hours and mins"
    return "%dh %dm" % (hours, (hours * 60) % 60)

CONFIG = dict(

    # The name of database
    DATABASE_NAME='nereid_project',

    # Tryton Config file path
    TRYTON_CONFIG='../etc/trytond.conf',

    # If the application is to be configured in the debug mode
    DEBUG=True,

    # The location where the translations of this template are stored
    TRANSLATIONS_PATH='i18n',

    SECRET_KEY=
        'secretkeygoeshere',

)
# Create a new application
app = Nereid(static_folder='%s/static/' % CWD, static_url_path='/static')

# Update the configuration with the above config values
app.config.update(CONFIG)

# Initialise the app, connect to cache and backend
app.initialise()
app.jinja_env.filters['float_to_time'] = float_to_time
app.jinja_env.globals.update({
    'datetime': datetime,
    'guess_mimetype': mimetypes.guess_type,
})

# Setup the filesystem cache
app.session_interface.session_store = FilesystemSessionStore(
    '/tmp', session_class=Session
)

Babel(app)
sentry = Sentry(app)


if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0')
