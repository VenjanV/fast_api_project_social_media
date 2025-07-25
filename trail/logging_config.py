import logging
from logging.config import dictConfig

from trail.config import DevConfig, config


def ofscated_email(email, ofescated_length):
    charec = email[:ofescated_length]
    first, last = email.split("@")
    return charec + ("*" * (len(first) - ofescated_length)) + "@" + last


class ofescated_email_filter(logging.Filter):
    def __init__(self, name: str = " ", ofescated_length: int = 2) -> None:
        super().__init__()
        self.ofescated_length = ofescated_length

    def filter(self, record: logging.LogRecord) -> bool:
        if "email" in record.__dict__():
            record.email = ofscated_email(record.email, self.ofescated_length)
        return True


def Config_logger() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if isinstance(config, DevConfig) else 32,
                    "default_value": "-",
                },
                "email": {
                    (): ofescated_email_filter,
                    "ofescated_length": 2 if isinstance(config, DevConfig) else 0,
                },
            },
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H%M%S",
                    "format": "(%(correlation_id)s)%(name)s:%(lineno)d - %(message)s",
                },
                # "file": {
                #     "class": "logging.Formatter",
                #     "datefmt": "%Y-%m-%dT%H%M%S",
                #     "format": "%(asctime)s.%(msecs)03dZ | %(levelname)-8s|[%(correlation_id)s]%(name)s:%(lineno)d - %(message)s",
                # },
                "file": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "datefmt": "%Y-%m-%dT%H%M%S",
                    "format": "%(asctime)s %(msecs)03d %(levelname)-8s %(correlation_id)s %(name)s %(lineno)d  %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id", "email"],
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "trail.log",
                    "encoding": "utf8",
                    "filters": ["correlation_id", "email"],
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default", "rotating_file"], "level": "INFO"},
                "trail": {
                    "handlers": ["default", "rotating_file"],
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "propagate": False,
                },
                "databases": {"handlers": ["default"], "level": "WARNING"},
                "aiosqlite": {"handlers": ["default"], "level": "WARNING"},
            },
        }
    )
