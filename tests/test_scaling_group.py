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

from mock import patch, Mock, MagicMock
from pyrax.autoscale import ScalingGroup as pyrax_ScalingGroup
from pyrax.fakes import FakeScalingGroup, FakeIdentity
import pyrax.exceptions
from raxas.enums import *
import requests

from tests.base_test import BaseTest
from raxas.scaling_group import ScalingGroup


class TestScalingGroup(BaseTest):
    def setUp(self):
        self.group_config = self._config_parsed['autoscale_groups']['group0']
        self._state = {
            'active': ['123-456-789-0000'],
            'desired_capacity': 1,
            'paused': False,
            'pending_capacity': 0,
            'active_capacity': 1
        }

    @patch('raxas.common.exit_with_error')
    def test_does_not_exit_with_valid_config(self, exit_mock):
        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(0, exit_mock.call_count, 'Exit with error SHOULD NOT be called')
        self.assertIsNotNone(scaling_group, 'scaling_group should not be None')
        self.assertEqual(self.group_config, scaling_group._config)

    @patch('raxas.common.exit_with_error')
    def test_does_exit_with_valid_config_missing_group(self, exit_mock):
        config = {
            "scale_up_policy": "scale up policy id",
            "scale_down_policy": "scale down policy id",
            "plugins": {}
        }
        scaling_group = ScalingGroup(config, 'group0')

        self.assertEqual(1, exit_mock.call_count, 'Exit with error not called')
        self.assertIsNotNone(scaling_group, 'scaling_group should not be None')

    @patch('raxas.common.exit_with_error')
    def test_does_exit_with_valid_config_missing_scale_up(self, exit_mock):
        config = {
            "group_id": "group id",
            "scale_down_policy": "scale down policy id",
            "plugins": {}
        }
        scaling_group = ScalingGroup(config, 'group0')

        self.assertEqual(1, exit_mock.call_count, 'Exit with error not called')
        self.assertIsNotNone(scaling_group, 'scaling_group should not be None')

    @patch('raxas.common.exit_with_error')
    def test_does_exit_with_valid_config_missing_scale_down(self, exit_mock):
        config = {
            "group_id": "group id",
            "scale_up_policy": "scale up policy id",
            "plugins": {}
        }
        scaling_group = ScalingGroup(config, 'group0')

        self.assertEqual(1, exit_mock.call_count, 'Exit with error not called')
        self.assertIsNotNone(scaling_group, 'scaling_group should not be None')

    @patch('raxas.common.exit_with_error')
    def test_does_not_exit_with_valid_config_missing_plugins(self, exit_mock):
        config = {
            "group_id": "group id",
            "scale_up_policy": "scale up policy id",
            "scale_down_policy": "scale down policy id"
        }
        scaling_group = ScalingGroup(config, 'group0')

        self.assertEqual(0, exit_mock.call_count, 'Exit with error called')
        self.assertIsNotNone(scaling_group, 'scaling_group should not be None')

    def test_plugin_config_returned_correctly(self):
        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(self.group_config['plugins'], scaling_group.plugin_config)

    def test_group_uuid_returned_correctly(self):
        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(self.group_config['group_id'], scaling_group.group_uuid)

    @patch('pyrax.autoscale')
    def test_scaling_group_returned_correctly(self, autoscale_mock):
        autoscale_mock.get.return_value = FakeScalingGroup()

        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertIsInstance(scaling_group.scaling_group, pyrax_ScalingGroup)
        autoscale_mock.get.assert_called_once_with(self.group_config['group_id'])

    @patch('pyrax.autoscale')
    def test_scaling_group_returns_none_on_exception(self, autoscale_mock):
        autoscale_mock.get.side_effect = pyrax.exceptions.NotFound(404)

        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertIsNone(scaling_group.scaling_group)
        autoscale_mock.get.assert_called_once_with(self.group_config['group_id'])

    @patch('pyrax.autoscale')
    def test_scaling_group_returns_from_cache(self, autoscale_mock):
        autoscale_mock.get.return_value = FakeScalingGroup()
        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertIsInstance(scaling_group.scaling_group, pyrax_ScalingGroup)

        autoscale_mock.get.return_value = 'Invalid!'
        self.assertIsInstance(scaling_group.scaling_group, pyrax_ScalingGroup)
        self.assertEqual(1, autoscale_mock.get.call_count)

    @patch.object(ScalingGroup, 'scaling_group')
    def test_state_returned_correctly(self, scaling_group_mock):
        scaling_group_mock.get_state.return_value = self._state

        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(scaling_group.state, self._state)

    @patch.object(ScalingGroup, 'scaling_group')
    def test_state_returns_none_on_attribute_exception(self, scaling_group_mock):
        scaling_group_mock.__get__ = Mock(return_value=None)

        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertIsNone(scaling_group.state)

    @patch.object(ScalingGroup, 'scaling_group')
    def test_state_returns_from_cache(self, scaling_group_mock):
        scaling_group_mock.get_state.return_value = self._state

        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertEqual(scaling_group.state, self._state)

        scaling_group_mock.get_state.return_value = 'Invalid!'
        self.assertEqual(scaling_group.state, self._state)

    @patch.object(ScalingGroup, 'state')
    def test_active_servers_returned_correctly(self, state_mock):
        state_mock.__get__ = Mock(return_value=self._state)

        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(scaling_group.active_servers, self._state['active'])

    @patch.object(ScalingGroup, 'state')
    def test_active_servers_returns_none_on_attribute_exception(self, state_mock):
        state_mock.__get__ = Mock(return_value=None)

        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual([], scaling_group.active_servers)

    @patch.object(ScalingGroup, 'state')
    def test_active_servers_returns_from_cache(self, state_mock):
        state_mock.__get__ = Mock(return_value=self._state)

        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertEqual(scaling_group.active_servers, self._state['active'])

        state_mock.__get__ = Mock(return_value='Invalid!')
        self.assertEqual(scaling_group.active_servers, self._state['active'])

    @patch.object(ScalingGroup, 'scaling_group')
    def test_launch_config_returned_correctly(self, scaling_group_mock):
        fake_launch_config = {'fake': 'launch_config'}
        scaling_group_mock.get_launch_config.return_value = fake_launch_config

        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(fake_launch_config, scaling_group.launch_config)

    @patch.object(ScalingGroup, 'scaling_group')
    def test_launch_config_attribute_exception(self, scaling_group_mock):
        scaling_group_mock.__get__ = Mock(return_value=None)

        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertIsNone(scaling_group.launch_config)

    @patch('raxas.common.get_machine_uuid', return_value=None)
    def test_is_master_cluster_no_uuid_error(self, get_machine_uuid_mock):
        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(NodeStatus.Unknown, scaling_group.is_master)

    @patch.object(ScalingGroup, 'active_servers')
    @patch('raxas.common.get_machine_uuid', return_value=123456)
    def test_is_master_cluster_invalid_active_error(self,
                                                    get_machine_uuid_mock,
                                                    active_servers_mock):
        scaling_group = ScalingGroup(self.group_config, 'group0')
        active_servers_mock.__get__ = Mock(return_value=[])

        self.assertEqual(NodeStatus.Unknown, scaling_group.is_master)

    @patch.object(ScalingGroup, 'active_servers')
    @patch('raxas.common.get_machine_uuid', return_value=123456)
    def test_is_master_cluster_one_active(self, get_machine_uuid_mock, active_servers_mock):
        active_servers_mock.__get__ = Mock(return_value=[123456])
        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(NodeStatus.Master, scaling_group.is_master)

    @patch.object(ScalingGroup, 'active_servers')
    @patch('raxas.common.get_machine_uuid', return_value=123456)
    def test_is_master_multiple_active_not_master(self, get_machine_uuid_mock, active_servers_mock):
        active_servers_mock.__get__ = Mock(return_value=[78910, 434987])
        scaling_group = ScalingGroup(self.group_config, 'group0')

        self.assertEqual(NodeStatus.Slave, scaling_group.is_master)

    @patch('requests.post')
    def test_webhook_call_status_200(self, post_mock):
        post_mock.return_value.status_code = 200
        scaling_group = ScalingGroup(self.group_config, 'group0')

        scaling_group.execute_webhook(ScaleDirection.Up, HookType.Post)
        self.assertEqual(post_mock.call_count, 1)

    @patch('raxas.common.get_logger')
    @patch('requests.post')
    def test_webhook_call_request_exception(self, post_mock, get_logger_mock):
        logger_mock = MagicMock(autospec=True)
        get_logger_mock.return_value = logger_mock
        post_mock.return_value.status_code = 500
        post_mock.side_effect = requests.exceptions.RequestException
        scaling_group = ScalingGroup(self.group_config, 'group0')

        scaling_group.execute_webhook(ScaleDirection.Down, HookType.Pre)
        self.assertEqual(post_mock.call_count, 2)
        self.assertEqual(logger_mock.error.call_count, 2)

    @patch.object(ScalingGroup, 'active_servers')
    def test_execute_policy_one_active(self, active_servers_mock):
        active_servers_mock.__get__ = MagicMock(return_value=[123456])
        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertEqual(ScaleEvent.NoAction, scaling_group.execute_policy(ScaleDirection.Down))

    @patch('pyrax.autoscale')
    @patch.object(ScalingGroup, 'active_servers')
    def test_execute_policy_pyrax_error(self, active_servers_mock, autoscale_mock):
        fake_scaling_group = MagicMock(spec=FakeScalingGroup)
        fake_scaling_group.get_policy.side_effect = pyrax.exceptions.PyraxException
        autoscale_mock.get.return_value = fake_scaling_group
        active_servers_mock.__get__ = MagicMock(return_value=[123456, 124590])
        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertEqual(ScaleEvent.Error, scaling_group.execute_policy(ScaleDirection.Down))

    @patch('pyrax.autoscale')
    @patch.object(ScalingGroup, 'active_servers')
    def test_execute_policy_success(self, active_servers_mock, autoscale_mock):
        fake_scaling_group = MagicMock(spec=FakeScalingGroup)
        autoscale_mock.get.return_value = fake_scaling_group
        active_servers_mock.__get__ = MagicMock(return_value=[123456, 124590])
        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertEqual(ScaleEvent.Success, scaling_group.execute_policy(ScaleDirection.Up))

    def test_get_webhook_values_returns_correctly(self):
        config_value = self.group_config['webhooks']['scale_up']['pre']
        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertEqual(config_value,
                         scaling_group.get_webhook_values(ScaleDirection.Up, HookType.Pre))

    @patch.object(ScalingGroup, 'check_config')
    @patch('raxas.common.get_logger')
    def test_get_webhook_values_key_error(self, get_logger_mock, config_mock):
        logger_mock = MagicMock(autospec=True)
        get_logger_mock.return_value = logger_mock
        config_mock.return_value = {'fake': 'config'}
        scaling_group = ScalingGroup(self.group_config, 'group0')
        scaling_group.get_webhook_values(ScaleDirection.Up, HookType.Post)
        self.assertEqual(1, logger_mock.error.call_count)

    def test_get_group_value_returns_correct(self):
        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertEqual(scaling_group.get_group_value('group_id'), self.group_config['group_id'])

    @patch('raxas.common.get_logger')
    def test_get_group_value_key_error(self, get_logger_mock):
        logger_mock = MagicMock(autospec=True)
        get_logger_mock.return_value = logger_mock
        scaling_group = ScalingGroup(self.group_config, 'group0')
        self.assertIsNone(scaling_group.get_group_value('fakeKey'))
        self.assertEqual(1, logger_mock.error.call_count)
