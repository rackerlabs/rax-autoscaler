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

import abc


class PluginBase(object):
    """ All plugins must inherit from this base class.

    from raxas.core_plugins.base import PluginBase
    class Yourplugin(PluginBase):
        def __init__(self, scaling_group, config, args):
        super(Yourplugin, self).__init__(scaling_group, config, args)

    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, scaling_group):
        """

        :param scaling_group: raxas.scaling_group.ScalingGroup
        """

    @abc.abstractproperty
    def name(self):
        """The name of the plugin as it appears in the configuration file."""

    @abc.abstractmethod
    def make_decision(self):
        """This function decides to scale up or scale down.

        :returns: 1    scale up
                  0    do nothing
                 -1    scale down
                  None No data available
        """
