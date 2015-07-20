# -*- coding: utf-8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# this file is part of 'RAX-AutoScaler'
#
# Copyright 2014 Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import logging


class ColouredConsoleHandler(logging.StreamHandler):
    '''
    console handler with ANSI colours support
    Usage example:

        def white_bold_underlined(self, msg):
            return self.decorate(self.BOLD + self.UNDERLINE +
                                 self.COLOR['white'], msg)

    ref: http://cwoebker.com/posts/ansi-escape-codes
    '''

    ESCAPE = '\033[%sm'
    ENDC = ESCAPE % '0'

    BOLD = '1;'
    FAINT = '2;'
    ITALIC = '3;'
    UNDERLINE = '4;'
    SLOW_BLINK = '5;'
    FAST_BLINK = '6;'

    COLOURS = {'black': '30',
               'red': '31',
               'green': '32',
               'yellow': '33',
               'blue': '34',
               'magenta': '35',
               'cyan': '36',
               'white': '37'}

    def __init__(self, stream=None):
        # run the regular Handler __init__
        logging.StreamHandler.__init__(self, None)

    def decorate(self, fmt, msg):
        format_sequence = self.ESCAPE % fmt
        return format_sequence + msg + self.ENDC

    def emit(self, record):
        # Need to make a actual copy of the record
        # to prevent altering the message for other loggers
        myrecord = copy.copy(record)

        levelno = myrecord.levelno
        if levelno >= 50:  # CRITICAL / FATAL
            myrecord.msg = self.decorate(self.BOLD + self.UNDERLINE +
                                         self.COLOURS['red'],
                                         str(myrecord.msg))
        elif levelno >= 40:  # ERROR
            myrecord.msg = self.decorate(self.COLOURS['red'],
                                         str(myrecord.msg))
        elif levelno >= 30:  # WARNING
            myrecord.msg = self.decorate(self.COLOURS['yellow'],
                                         str(myrecord.msg))
        elif levelno >= 20:  # INFO
            myrecord.msg = self.decorate(self.COLOURS['green'],
                                         str(myrecord.msg))
        elif levelno >= 10:  # DEBUG
            myrecord.msg = self.decorate(self.COLOURS['blue'],
                                         str(myrecord.msg))
        else:  # NOTSET and anything else
            myrecord.msg = self.decorate(self.COLOURS['grey'],
                                         str(myrecord.msg))
        logging.StreamHandler.emit(self, myrecord)
