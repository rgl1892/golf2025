"""
Logging Configuration

Centralized logging configuration for the golf2025 application.
Provides different log levels and handlers for development and production.
"""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / 'logs'

# Create logs directory if it doesn't exist
LOG_DIR.mkdir(exist_ok=True)

# Determine if we're in DEBUG mode
DEBUG = os.getenv('DEBUG', 'True') == 'True'


def get_logging_config():
    """
    Get logging configuration based on environment.
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} - {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'simple': {
                'format': '[{levelname}] {message}',
                'style': '{',
            },
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            } if not DEBUG else {
                'format': '[{levelname}] {message}',
                'style': '{',
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG' if DEBUG else 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose' if DEBUG else 'simple',
            },
            'file_general': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_DIR / 'golf2025.log',
                'maxBytes': 1024 * 1024 * 10,  # 10MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'file_errors': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_DIR / 'errors.log',
                'maxBytes': 1024 * 1024 * 10,  # 10MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'file_requests': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_DIR / 'requests.log',
                'maxBytes': 1024 * 1024 * 10,  # 10MB
                'backupCount': 3,
                'formatter': 'verbose',
                'filters': ['require_debug_false'],
            },
            'file_security': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_DIR / 'security.log',
                'maxBytes': 1024 * 1024 * 10,  # 10MB
                'backupCount': 10,
                'formatter': 'verbose',
            },
            'mail_admins': {
                'level': 'ERROR',
                'class': 'django.utils.log.AdminEmailHandler',
                'filters': ['require_debug_false'],
                'formatter': 'verbose',
            },
        },
        'loggers': {
            # Django core loggers
            'django': {
                'handlers': ['console', 'file_general'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'file_errors', 'mail_admins'],
                'level': 'ERROR',
                'propagate': False,
            },
            'django.security': {
                'handlers': ['console', 'file_security', 'mail_admins'],
                'level': 'WARNING',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['console'] if DEBUG else [],
                'level': 'DEBUG' if DEBUG else 'WARNING',
                'propagate': False,
            },
            # Application loggers
            'superb_ock': {
                'handlers': ['console', 'file_general'],
                'level': 'DEBUG' if DEBUG else 'INFO',
                'propagate': False,
            },
            'superb_ock.errors': {
                'handlers': ['console', 'file_errors', 'mail_admins'],
                'level': 'ERROR',
                'propagate': False,
            },
            'superb_ock.requests': {
                'handlers': ['file_requests'],
                'level': 'INFO',
                'propagate': False,
            },
            'superb_ock.security': {
                'handlers': ['console', 'file_security', 'mail_admins'],
                'level': 'WARNING',
                'propagate': False,
            },
            # Service-specific loggers
            'superb_ock.services.media': {
                'handlers': ['console', 'file_general'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file_general'],
            'level': 'INFO',
        },
    }


# Export the configuration
LOGGING = get_logging_config()
