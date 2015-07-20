#!/usr/bin/env python
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
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=R0903

import enum


class NodeStatus(enum.Enum):
    Master = 1
    Slave = 2
    Unknown = 3


class ScaleEvent(enum.Enum):
    Success = 1
    Error = 2
    NoAction = 3
    NotMaster = 4


class ScaleDirection(enum.Enum):
    Down = -1
    Nothing = 0
    Up = 1


class HookType(enum.Enum):
    Pre = 1
    Post = 2
