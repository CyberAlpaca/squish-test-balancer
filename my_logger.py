# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Cyber Alpaca
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import logging


class ColorFormatter(logging.Formatter):
    # Define color codes
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[34;20m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"

    # Define the base format
    format_str = "%(asctime)s [%(levelname)s] "

    # Map log levels to colors
    FORMATS = {
        logging.DEBUG: blue + format_str + reset + "%(message)s",
        logging.INFO: format_str + reset + "%(message)s",
        logging.WARNING: yellow + format_str + reset + "%(message)s",
        logging.ERROR: red + format_str + reset + "%(message)s",
        logging.CRITICAL: bold_red + format_str + reset + "%(message)s",
    }

    def format(self, record):
        # Get the appropriate format based on the log level
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setFormatter(ColorFormatter())
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)
