"""
This file is used to set up general functionality.
"""

import logging
import os

""" Register log level 'TRACE' """
logging.TRACE = 5
logging.addLevelName(logging.TRACE, "TRACE")


def trace(self, message, *args, **kws):
    if self.isEnabledFor(logging.TRACE):
        self._log(logging.TRACE, message, args, **kws)


logging.Logger.trace = trace
logger = logging.getLogger()

if (len(logger.handlers) == 0):
    handler = logging.StreamHandler()
    handler.setLevel(logging.TRACE)

    formatter = logging.Formatter('%(asctime)s - %(name)s: %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.setLevel(logging.TRACE)
    logger.propagate = False
    logger.addHandler(handler)


def toAbsolutePath(path):
    """ Add function to 'os.path' to transform a relative path to an absolute one """
    if (path.startswith("..")):
        return os.path.join(os.path.dirname(__file__), path)
    return path


os.path.toAbsolutePath = toAbsolutePath
