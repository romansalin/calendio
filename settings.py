import os
import logging.config
import uuid
import base64

from tornado.options import define, options
from jinja2 import Environment, FileSystemLoader
import motor


# Paths
ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(ROOT, 'static')
TEMPLATE_ROOT = os.path.join(ROOT, 'templates')

define('port', default=8000, help='run on the given port', type=int)
define('config', default=None, help='tornado config file')
define('debug', default=True, help='debug mode', type=bool)
options.parse_command_line()

# DB
MONGO_DB = {
    'host': 'localhost',
    'port': 27017,
    'db_name': 'calendio',
}

# Application settings
APP_SETTINGS = {
    'debug': options.debug,
    'template_path': TEMPLATE_ROOT,
    'static_path': STATIC_ROOT,
    'cookie_secret': base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
    'xsrf_cookies': True,
    'login_url': '/login',
    'db': motor.MotorClient(MONGO_DB['host'],
                            MONGO_DB['port'])[MONGO_DB['db_name']],
}

# Sessions
SESSION_STORE = {
    'pycket': {
        'engine': 'redis',
        'storage': {
            'host': 'localhost',
            'port': 6379,
            'db_sessions': 10,
            'db_notifications': 11,
            'max_connections': 2 ** 31,
        },
        'cookies': {
            'expires_days': 30,
        }
    }
}

APP_SETTINGS.update(SESSION_STORE)

# Template
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATE_ROOT),
                        auto_reload=options.debug,
                        autoescape=False)

# Logging
if options.debug:
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'main_formatter': {
            'format': '%(levelname)s:%(name)s: %(message)s '
            '(%(asctime)s; %(filename)s:%(lineno)d)',
            'datefmt': "%Y-%m-%d %H:%M:%S",
        },
        'console_formatter': {
            'format': '%(message)s',
        },
    },
    'handlers': {
        'rotate_file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(ROOT, 'logs/main.log'),
            'when': 'midnight',
            'interval': 1,  # day
            'backupCount': 7,
            'formatter': 'main_formatter',
        },
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'console_formatter',
        },
    },
    'loggers': {
        '': {
            'handlers': ['rotate_file', 'console'],
            'level': LOG_LEVEL,
        }
    }
}

logging.config.dictConfig(LOGGING)

if options.config:
    options.parse_config_file(options.config)
