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

from __future__ import with_statement

from mock import patch, PropertyMock, MagicMock

from tests.base_test import BaseTest
from raxas import monitoring
from raxas.scaling_group import ScalingGroup
from pyrax import fakes
from pyrax.cloudmonitoring import CloudMonitorEntity
from pyrax.cloudmonitoring import CloudMonitorCheck


class MonitoringTest(BaseTest):
    def __init__(self, *args, **kwargs):
        super(MonitoringTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.scaling_group = MagicMock(spec=ScalingGroup)
        self.scaling_group.plugin_config = {'raxmon_autoscale': {
            'check_type': 'agent.plugin'}}
        self.scaling_group.state = {'active_capacity': 1}
        self.scaling_group.active_servers = ['server1']

    @patch('pyrax.cloud_monitoring')
    def test_add_entity_check(self, mock_cloud_monitoring):
        """ Tests that entity.create_check is called if there
            is no check matching the requested one on the entity
            passed
        """
        self.scaling_group.active_servers = ['server1']

        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'server1'})

        entity = MagicMock(spec=CloudMonitorEntity)
        agent_id = PropertyMock(return_value='server1')
        type(entity).agent_id = agent_id

        class mock_ipaddr(object):
            def values(self):
                return ['1.1.1.1', '2.2.2.2']
        mock_ip = mock_ipaddr()
        type(entity).ip_addresses = mock_ip

        check = MagicMock(spec=CloudMonitorCheck)
        check_type = PropertyMock(return_value='NOTagent.plugin')
        type(check).type = check_type
        check.get_metric_data_points.return_value = [{'average': -1}]

        entity.create_check = MagicMock()
        monitoring.add_entity_checks([entity], 'agent.plugin', 'inconsequenial')

        entity.create_check.assert_called_once()

    @patch('pyrax.cloud_monitoring')
    def test_skip_add_entity_check(self, mock_cloud_monitoring):
        """ Tests that entity.create_check is NOT called if there already
            is a check matching the requested one on the entity
            passed
        """
        self.scaling_group.active_servers = ['server1']

        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'server1'})

        entity = MagicMock(spec=CloudMonitorEntity)
        agent_id = PropertyMock(return_value='server1')
        type(entity).agent_id = agent_id

        class mock_ipaddr(object):
            def values(self):
                return ['1.1.1.1', '2.2.2.2']
        mock_ip = mock_ipaddr()
        type(entity).ip_addresses = mock_ip

        check = MagicMock(spec=CloudMonitorCheck)
        check_type = PropertyMock(return_value='agent.plugin')
        type(check).type = check_type
        check.get_metric_data_points.return_value = [{'average': -1}]
        entity.list_checks.return_value = [check]

        entity.create_check = MagicMock()
        monitoring.add_entity_checks([entity], 'agent.plugin', 'scale_me')

        self.assertFalse(entity.create_check.called)

    @patch('pyrax.cloud_monitoring')
    def test_return_entities(self, mock_cloud_monitoring):
        """ Test that monitoring.get_entities() returns entities that are
            active in the scaling group
        """
        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'server1'})
        mock_cloud_monitoring.list_entities.return_value = [entity]
        self.assertEqual(monitoring.get_entities(self.scaling_group), [entity])


    @patch('pyrax.cloud_monitoring')
    def test_return_no_entities(self, mock_cloud_monitoring):
        """ Test that monitoring.get_entities() ONLY returns entities that are
            active in the scaling group
        """
        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'NOTINASGRP'})
        mock_cloud_monitoring.list_entities.return_value = [entity]
        self.assertNotEqual(monitoring.get_entities(self.scaling_group), [entity])

