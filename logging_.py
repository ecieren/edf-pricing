import datetime
import logging
import os
import sys
from inspect import getframeinfo, stack
from logging.handlers import RotatingFileHandler

# remove big logs from matpltolib
logging.getLogger("matplotlib.font_manager").disabled = True

_logname = "mainlog_"


def getLogger():
    return logging.getLogger(_logname)


def now():
    """get utc time now (datetime format, utc)"""
    return datetime.datetime.now(datetime.timezone.utc)


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors"""

    def __init__(self, fmt="%(message)s", datefmt="%Y-%m-%d %H:%M:%S", color=True):
        if color:
            blue = "\x1b[34;22m"
            grey = "\x1b[38;22m"
            yellow = "\x1b[33;22m"
            red = "\x1b[31;22m"
            magenta = "\x1b[35;22m"
            reset = "\x1b[0m"
        else:
            blue = ""
            grey = ""
            yellow = ""
            red = ""
            magenta = ""
            reset = ""
        self.FORMATS = {
            logging.DEBUG: blue + fmt + reset,
            logging.INFO: grey + fmt + reset,
            logging.WARNING: yellow + fmt + reset,
            logging.ERROR: red + fmt + reset,
            logging.CRITICAL: magenta + fmt + reset,
        }
        self.datefmt = datefmt
        return

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        return formatter.format(record)


class StreamToLogger(object):
    """fake file-like stream object that redirects writes to a logger instance"""

    def __init__(self, logger, log_level=logging.DEBUG):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


def _str2level(strin):
    """convert string to logging level"""
    if strin == "debug":
        return logging.DEBUG
    elif strin == "info":
        return logging.INFO
    elif strin == "warning":
        return logging.WARNING
    elif strin == "error":
        return logging.ERROR
    elif strin == "critical":
        return logging.CRITICAL
    else:
        raise ValueError("Input string does not match predefined logging level")


def _check(cfg):
    """Check data in logging config for basic typo/errors."""

    keyl = [
        "period",
        "logfile",
        "logfilelevel",
        "logfilename",
        "logfilesize",
        "logfilenum",
        "logstream",
        "logstreamlevel",
    ]
    typl = [int, bool, str, str, int, int, bool, str]

    for k, t in zip(keyl, typl):
        if not isinstance(cfg[k], t):
            raise TypeError(f"key {k} must be an instance of type {t}")

    for key in [keyl[i] for i in [0, 4, 5]]:
        if cfg[key] < 0:
            raise ValueError(f"input {key} must be positive")

    return


def init(cfg):
    """create a logger object with specific parameters; some of them can be
    edited through a config file
    """
    # check input types
    _check(cfg)

    # create logger object, set ot lowest level (so that everything is tracked)
    logger = getLogger()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # test config to know whether write a log file, adjust level
    if cfg["logfile"]:
        file_handler = RotatingFileHandler(
            cfg["logfilename"],
            maxBytes=cfg["logfilesize"],
            backupCount=cfg["logfilenum"],
            encoding="utf-8",
        )
        file_handler.setLevel(_str2level(cfg["logfilelevel"]))
        file_handler.setFormatter(CustomFormatter(color=False))
        logger.addHandler(file_handler)

    # test config to know whether write a log stream, adjust level
    if cfg["logstream"]:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(_str2level(cfg["logstreamlevel"]))
        stream_handler.setFormatter(CustomFormatter(color=True))
        logger.addHandler(stream_handler)

    # redirect stderr to logger
    sl = StreamToLogger(logger, logging.ERROR)
    sys.stderr = sl

    return


def finalize():
    """use this to properly end a logger (usefull in spyder)"""
    logger = getLogger()
    handlers = logger.handlers[:]
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)
    return


def _format(lvl: str, msg: str, where: str = ""):
    ts = now().isoformat(sep=" ", timespec="milliseconds")
    s = (8 - len(lvl)) * " "
    return f"[{ts}] <{lvl}> {s}{msg}{where}"


def debug(msg: str):
    caller = getframeinfo(stack()[1][0])
    where = " {%s:%d}" % (os.path.basename(caller.filename), caller.lineno)
    return getLogger().debug(_format("debug", msg, where=where))


def info(msg: str):
    return getLogger().info(_format("info", msg))


def warning(msg: str):
    return getLogger().warning(_format("warning", msg))


def error(msg: str):
    return getLogger().error(_format("error", msg))


def critical(msg: str):
    return getLogger().critical(_format("critical", msg))


if __name__ == "__main__":

    # TEST: write random string with random levels on file and stdout

    cfg = dict(
        logfile=True,
        logfilename="/tmp/toto.log",
        logfilelevel="info",
        logstream=True,
        logstreamlevel="debug",
        period=999999,
        logfilesize=10485760,
        logfilenum=2,
    )

    init(cfg)

    import numpy as np
    import random
    import string
    import time

    for i in range(16):
        msg = "".join(random.choice(string.ascii_letters) for m in range(32))

        lvl = np.random.randint(5)
        if lvl == 0:
            debug(msg)
        elif lvl == 1:
            info(msg)
        elif lvl == 2:
            warning(msg)
        elif lvl == 3:
            error(msg)
        elif lvl == 4:
            critical(msg)
        else:
            raise ValueError("Level value not in list")
        time.sleep(np.random.rand())

    finalize()
