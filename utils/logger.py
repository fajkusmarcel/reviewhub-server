# utils/app_logger.py
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import has_request_context, g, session

LOGGER_NAME = "reviewhub"

class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # USER
        user = "-"
        try:
            if has_request_context():
                user = (
                    getattr(g, "user_login", None)
                    or session.get("user_login")
                    or " ".join(x for x in [session.get("user_name"), session.get("user_surname")] if x)
                    or session.get("user_id")
                    or "-"
                )
        except Exception:
            # nechceme, aby logging shodil request
            user = "-"
        record.user_login = user

        # TYPE
        record.event_type = getattr(record, "event_type", "-")
        return True


def setup_logging(log_dir: str = "/var/log/virtualserver", level: int = logging.INFO):
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    if logger.handlers:
        return logger

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "reviewhub.log")

    fmt = logging.Formatter(
        "%(asctime)s '%(user_login)s' [%(levelname)s] [%(event_type)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=5)
    fh.setLevel(level); fh.setFormatter(fmt); fh.addFilter(ContextFilter())

    sh = logging.StreamHandler()
    sh.setLevel(level); sh.setFormatter(fmt); sh.addFilter(ContextFilter())

    logger.addHandler(fh); logger.addHandler(sh)
    return logger

def _log(level: int, event_type: str, message: str):
    logging.getLogger(LOGGER_NAME).log(level, message, extra={"event_type": event_type})

def log_info(event_type: str, message: str):    _log(logging.INFO, event_type, message)
def log_warning(event_type: str, message: str): _log(logging.WARNING, event_type, message)
def log_error(event_type: str, message: str):   _log(logging.ERROR, event_type, message)

def log_exception(event_type: str, message: str):
    logging.getLogger("reviewhub").exception(message, extra={"event_type": event_type})
