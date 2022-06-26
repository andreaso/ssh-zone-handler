"""Static configuration"""

from typing import Any, Final

LOGCONF: Final[dict[str, Any]] = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "console": {
            "format": "%(message)s",
        },
        "syslog": {
            "format": "ssh-zone-handler[%(process)d]: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "console",
        },
        "syslog": {
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "level": "DEBUG",
            "formatter": "syslog",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "syslog"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
