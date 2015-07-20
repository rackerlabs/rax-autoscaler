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
import json
import requests
import requests.exceptions
import pyrax
import pyrax.exceptions

from raxas import common
from raxas import enums


class ScalingGroup(object):
    def __init__(self, config, group_name):
        """Instantiate a ScalingGroup object.

        :param config: Configuration dict for this scaling group
        :param group_name: Name of the group to print in the log file
        """
        self._group_name = group_name
        self._config = self.check_config(config)

        self._scaling_group = None
        self._servers_state = None
        self._active_servers = None

    @classmethod
    def check_config(cls, config):
        logger = common.get_logger()

        if None in [
                config.get('group_id'),
                config.get('scale_up_policy'),
                config.get('scale_down_policy')]:
            common.exit_with_error('Invalid group configuration')
        if None in [
                config.get('plugins')]:
            logger.warn('DeprecationWarning: You are using a deprecated config file please update'
                        ' your configuration file to v0.3 standard.')
            return config
        else:
            return config

    @property
    def plugin_config(self):
        if self._config.get('plugins') is None:
            self._config['plugins'] = \
                {
                    'raxmon':
                    {
                        'scale_up_threshold': self._config.get('scale_up_threshold', 0.6),
                        'scale_down_threshold': self._config.get('scale_down_threshold', 0.4),
                        'check_config': self._config.get('check_config', '{}'),
                        'metric_name': self._config.get('metric_name', '1m'),
                        'check_type': self._config.get('check_type', 'agent.load_average')
                    }
                }
        return self._config.get('plugins')

    @property
    def group_uuid(self):
        return self.get_group_value('group_id')

    @property
    def launch_config(self):
        try:
            return self.scaling_group.get_launch_config()
        except AttributeError:
            return None

    @property
    def scaling_group(self):
        if self._scaling_group is None:
            logger = common.get_logger()
            autoscale_api = pyrax.autoscale

            try:
                self._scaling_group = autoscale_api.get(self.group_uuid)
            except pyrax.exc.PyraxException as error:
                logger.error('Error: Unable to get scaling group \'%s\': %s',
                             self.group_uuid, error)
                return None
            else:
                return self._scaling_group
        else:
            return self._scaling_group

    @property
    def state(self):
        if self._servers_state is None:
            try:
                self._servers_state = self.scaling_group.get_state()
            except AttributeError:
                return None
            else:
                return self._servers_state
        else:
            return self._servers_state

    @property
    def active_servers(self):
        if self._active_servers is None:
            try:
                self._active_servers = self.state.get('active', [])
            except AttributeError:
                return []
            else:
                return self._active_servers
        else:
            return self._active_servers

    @property
    def is_master(self):
        """This property checks scaling group state and determines if this node is a master.

        :returns: enums.NodeStatus
        """
        logger = common.get_logger()
        masters = []
        node_id = common.get_machine_uuid(self)

        if node_id is None:
            logger.error('Failed to get server uuid')
            return enums.NodeStatus.Unknown

        active_count = len(self.active_servers)
        if active_count == 1:
            masters.append(self.active_servers[0])
        elif active_count > 1:
            masters.append(self.active_servers[0])
            masters.append(self.active_servers[1])
        else:
            logger.error('Unknown cluster state')
            return enums.NodeStatus.Unknown

        if node_id in masters:
            logger.info('Node is a master, continuing')
            return enums.NodeStatus.Master
        else:
            logger.info('Node is not a master, nothing to do. Exiting')
            return enums.NodeStatus.Slave

    def get_group_value(self, key):
        """This function returns value in autoscale_groups section associated with
           provided key.

          :param key: key name
          :returns: value associated with key
        """
        logger = common.get_logger()

        value = self._config.get(key.lower())
        if value is None:
            logger.error('Error: unable to get value for key "%s" in group "%s"',
                         key, self._group_name)

        return value

    def get_webhook_values(self, policy, hook):
        """This function returns value in webhooks section of json file which is
           associated with provided key.

          :param policy: raxas.enums.ScaleDirection
          :param hook: raxas.enums.HookType
          :returns: value associated with key

        """
        logger = common.get_logger()

        policy = 'scale_%s' % policy.name.lower()
        hook = hook.name.lower()

        try:
            return self._config['webhooks'][policy][hook]
        except KeyError:
            logger.error('Error: unable to get config value for '
                         '[\'%s\'][\'webhooks\'][\'%s\'][\'%s\']',
                         self._group_name, policy, hook)
            return None

    def execute_webhook(self, policy, hook):
        """This function makes webhook calls.

        :param policy: raxas.enums.ScaleDirection
        :param hook: raxas.enums.HookType
        """
        logger = common.get_logger()

        logger.info('Executing webhook: scale_%s:%s', policy.name, hook.name)
        urls = self.get_webhook_values(policy, hook)
        data = json.dumps(self._config)

        for url in urls:
            logger.info('Sending POST request to url: \'%s\'', url)
            try:
                response = requests.post(url, json=data)
                logger.info('Received status code %d from url: \'%s\'', response.status_code, url)
            except requests.exceptions.RequestException as error:
                logger.error(error)

    def execute_policy(self, policy):
        """

        :param policy: raxas.enums.ScaleDirection
        :returns: True
                  False
        """
        logger = common.get_logger()

        policy_id = self.get_group_value('scale_%s_policy' % policy.name)

        if len(self.active_servers) == 1 and policy == enums.ScaleDirection.Down:
            logger.info('Current active server count is 1, will not scale down')
            return enums.ScaleEvent.NoAction

        try:
            self.scaling_group.get_policy(policy_id).execute()
        except pyrax.exceptions.PyraxException as error:
            logger = common.get_logger()
            logger.error('Error scaling %s: %s', policy.name, error)
            return enums.ScaleEvent.Error
        else:
            return enums.ScaleEvent.Success
