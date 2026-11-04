import logging, os
from logging.handlers import RotatingFileHandler


def get_logger(name: str = "sentiment") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    try:
        os.makedirs("logs", exist_ok=True)
        fh = RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=2)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:  # read-only FS in some clouds: console only
        pass
    return logger
