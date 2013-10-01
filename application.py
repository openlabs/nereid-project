# Activate the virutalenv
import os
cwd = os.path.abspath(os.path.dirname(__file__))
app_root_path = os.path.dirname(os.path.join(cwd, ''))
activate_this = '%s/bin/activate_this.py' % app_root_path
execfile(activate_this, dict(__file__=activate_this))

import random
import datetime

from nereid import Nereid
from werkzeug.contrib.sessions import FilesystemSessionStore
from nereid.sessions import Session
from nereid.contrib.locale import Babel
import simplejson as json
from raven import Client
from raven.middleware import Sentry


os.environ['PYTHON_EGG_CACHE'] = '%s/.egg_cache' % app_root_path

print '%s/static/' % cwd

CONFIG = dict(

    # The name of database
    DATABASE_NAME='openlabs_tryton',

    EMAIL_FROM='info@openlabs.co.in',
    # Static file root. The root location of the static files. The static/ will
    # point to this location. It is recommended to use the web server to serve
    # static content
    STATIC_FILEROOT='%s/static/' % cwd,

    # Tryton Config file path
    TRYTON_CONFIG='%s/etc/trytond.conf' % app_root_path,

    # Cache backend type
    #CACHE_TYPE = 'werkzeug.contrib.cache.MemcachedCache',

    # Cache Memcached Servers
    # (Only if SESSION_STORE_CLASS or CACHE_TYPE is Memcached)
    # eg: ['localhost:11211']
    #CACHE_MEMCACHED_SERVERS = ['localhost:11211'],
    #CACHE_MEMCACHED_SERVERS = ['mc1:11211', 'mc2:11211'],

    # If the application is to be configured in the debug mode
    DEBUG=False,

    TEMPLATE_LOADER_CLASS='nereid.templating.FileSystemLoader',
    TEMPLATE_SEARCH_PATH='%s' % cwd,
    TRANSLATIONS_PATH='%s/i18n/' % cwd,
)

app = Nereid()
app.config.update(CONFIG)
app.initialise()
app.jinja_env.globals.update({
    'json': json,
    'sample': random.sample,
    'datetime': datetime,
})


def float_to_time(hours):
    "Converts a float of hours into readable hours and mins"
    return "%dh %dm" % (hours, (hours * 60) % 60)

app.jinja_env.filters['float_to_time'] = float_to_time

babelized_app = Babel(app)
application = babelized_app.app.wsgi_app

application = Sentry(
    application, Client(
        'http://2d6a2e5316fb481993b3eeb6123d7203:'
        '80855a8b88354bf5acca271f574b79db@sentry.openlabs.co.in/10'
    )
)

# If the file is launched from the CLI then launch the app using the debug
# web server built into werkzeug
if __name__ == '__main__':
    class NereidTestMiddleware(object):
        def __init__(self, app, site):
            self.app = app
            self.site = site

        def __call__(self, environ, start_response):
            environ['HTTP_HOST'] = self.site
            return self.app(environ, start_response)
    site = 'my.openlabs.co.in:5000'
    app.wsgi_app = NereidTestMiddleware(app.wsgi_app, site)
    app.debug = False
    app.static_folder = '%s/static' % (cwd,)
    app.session_interface.session_store = \
        FilesystemSessionStore('/tmp', session_class=Session)
    app.run('0.0.0.0')
