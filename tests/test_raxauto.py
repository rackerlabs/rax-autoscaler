# -*- coding: utf-8 -*-

# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# this file is part of 'RAX-AutoScaler'
#
# Copyright 2015 Rackspace US, Inc.
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

import unittest2

from mock import MagicMock, PropertyMock, patch
from pyrax.cloudloadbalancers import CloudLoadBalancer
from pyrax.cloudloadbalancers import Node
from pyrax.cloudmonitoring import CloudMonitorCheck
from pyrax.cloudmonitoring import CloudMonitorEntity
from pyrax import fakes
from raxas.core_plugins.raxmon_autoscale import Raxmon_autoscale
from raxas.scaling_group import ScalingGroup


@patch('pyrax.cloud_monitoring', create=True)
class Raxmon_autoscaleTest(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(Raxmon_autoscaleTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.scaling_group = MagicMock(spec=ScalingGroup)
        self.scaling_group.plugin_config = {'raxmon_autoscale': {
            'load_balancers': [12345, 67889],
            'num_static_servers': 0,
            'check_type': 'agent.plugin'}}
        self.scaling_group.state = {'active_capacity': 1}
        self.scaling_group.active_servers = ['server1']

    @patch('pyrax.cloud_loadbalancers')
    def test_static_lb_nodes_do_nothing(self, fake_clb, mock_cloud_monitoring):
        """ Tests the functionality that allows static servers to be in the
            same LB as the autoscaled nodes.
            Active nodes in LB is one, and only one node in AS group, but also
            a static server - should refuse to scale down even though result
            is -1.
        """
        self.scaling_group.plugin_config = {'raxmon_autoscale': {
            'load_balancers': [12345],
            'check_type': 'agent.plugin',
            'num_static_servers': 1}}

        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'server1'})

        entity = MagicMock(spec=CloudMonitorEntity)
        agent_id = PropertyMock(return_value='server1')
        type(entity).agent_id = agent_id

        check = MagicMock(spec=CloudMonitorCheck)
        check_type = PropertyMock(return_value='agent.plugin')
        type(check).type = check_type
        check.get_metric_data_points.return_value = [{'average': -1}]

        entity.list_checks.return_value = [check]
        mock_cloud_monitoring.list_entities.return_value = [entity]

        fake_lb = MagicMock(spec=CloudLoadBalancer)
        fake_node = MagicMock(spec=Node)
        fake_node_status = PropertyMock(return_value='ONLINE')
        fake_node_condition = PropertyMock(return_value='ENABLED')
        type(fake_node).status = fake_node_status
        type(fake_node).condition = fake_node_condition

        lb_nodes = PropertyMock(return_value=[fake_node])
        fake_clb.get.return_value = fake_lb
        type(fake_lb).nodes = lb_nodes

        raxmon_autoscale = Raxmon_autoscale(self.scaling_group)
        self.assertEquals(raxmon_autoscale.make_decision(), 0)
        self.scaling_group.plugin_config['num_static_servers'] = 0

    @patch('pyrax.cloud_loadbalancers')
    def test_static_lb_nodes_scale_down(self, fake_clb, mock_cloud_monitoring):
        """ Tests the functionality that allows static servers to be in the
            same LB as the autoscaled nodes.
            Active nodes in LB is three, but only one node in AS group -
            should still scale down.
            (In a live situation in this scenario
             raxas.scaling_group.execute_policy will overrule this ruling)
        """
        self.scaling_group.plugin_config = {'raxmon_autoscale': {
            'load_balancers': [12345],
            'check_type': 'agent.plugin',
            'num_static_servers': 1}}

        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'server1'})

        entity = MagicMock(spec=CloudMonitorEntity)
        agent_id = PropertyMock(return_value='server1')
        type(entity).agent_id = agent_id

        check = MagicMock(spec=CloudMonitorCheck)
        check_type = PropertyMock(return_value='agent.plugin')
        type(check).type = check_type
        check.get_metric_data_points.return_value = [{'average': -1}]

        entity.list_checks.return_value = [check]
        mock_cloud_monitoring.list_entities.return_value = [entity]

        fake_nodes = []
        fake_lb = MagicMock(spec=CloudLoadBalancer)
        for i in range(3):
            fake_nodes.append(MagicMock(spec=Node))
            fake_node_status = PropertyMock(return_value='ONLINE')
            fake_node_condition = PropertyMock(return_value='ENABLED')
            type(fake_nodes[i]).status = fake_node_status
            type(fake_nodes[i]).condition = fake_node_condition

        lb_nodes = PropertyMock(return_value=fake_nodes)
        fake_clb.get.return_value = fake_lb
        type(fake_lb).nodes = lb_nodes

        raxmon_autoscale = Raxmon_autoscale(self.scaling_group)
        self.assertEquals(raxmon_autoscale.make_decision(), -1)
        self.scaling_group.plugin_config['num_static_servers'] = 0

    @patch('pyrax.cloud_loadbalancers')
    def test_make_decision_equal_nodes_two_lbs(self, fake_clb,
                                               mock_cloud_monitoring):
        """ Tests one healthy server in LB and one active server in
            scaling group with a decision to scale down. Result should be
            scale down (-1)
        """
        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'server1'})

        entity = MagicMock(spec=CloudMonitorEntity)
        agent_id = PropertyMock(return_value='server1')
        type(entity).agent_id = agent_id

        check = MagicMock(spec=CloudMonitorCheck)
        check_type = PropertyMock(return_value='agent.plugin')
        type(check).type = check_type
        check.get_metric_data_points.return_value = [{'average': -1}]

        entity.list_checks.return_value = [check]
        mock_cloud_monitoring.list_entities.return_value = [entity]

        fake_lb = MagicMock(spec=CloudLoadBalancer)
        fake_node_a = MagicMock(spec=Node)
        fake_node_status = PropertyMock(return_value='ONLINE')
        fake_node_condition = PropertyMock(return_value='ENABLED')
        type(fake_node_a).status = fake_node_status
        type(fake_node_a).condition = fake_node_condition

        lb_nodes = PropertyMock(return_value=[fake_node_a])
        fake_clb.get.return_value = fake_lb
        type(fake_lb).nodes = lb_nodes

        raxmon_autoscale = Raxmon_autoscale(self.scaling_group)
        self.assertEquals(raxmon_autoscale.make_decision(), -1)

    @patch('pyrax.cloud_loadbalancers')
    def test_make_decision_equal_nodes_single_lb(self, fake_clb,
                                                 mock_cloud_monitoring):
        """ Tests one healthy server in LB and one active server in
            scaling group with a decision to scale down. Result should be
            scale down (-1)
        """

        self.scaling_group.plugin_config = {'raxmon_autoscale': {
            'load_balancers': [12345],
            'check_type': 'agent.plugin'}}

        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'server1'})

        entity = MagicMock(spec=CloudMonitorEntity)
        agent_id = PropertyMock(return_value='server1')
        type(entity).agent_id = agent_id

        check = MagicMock(spec=CloudMonitorCheck)
        check_type = PropertyMock(return_value='agent.plugin')
        type(check).type = check_type
        check.get_metric_data_points.return_value = [{'average': -1}]

        entity.list_checks.return_value = [check]
        mock_cloud_monitoring.list_entities.return_value = [entity]

        fake_lb = MagicMock(spec=CloudLoadBalancer)
        fake_node_a = MagicMock(spec=Node)
        fake_node_status = PropertyMock(return_value='ONLINE')
        fake_node_condition = PropertyMock(return_value='ENABLED')
        type(fake_node_a).status = fake_node_status
        type(fake_node_a).condition = fake_node_condition

        lb_nodes = PropertyMock(return_value=[fake_node_a])
        fake_clb.get.return_value = fake_lb
        type(fake_lb).nodes = lb_nodes

        raxmon_autoscale = Raxmon_autoscale(self.scaling_group)
        self.assertEquals(raxmon_autoscale.make_decision(), -1)

    @patch('pyrax.cloud_loadbalancers')
    def test_make_decision_no_nodes_single_lb(self, fake_clb,
                                              mock_cloud_monitoring):
        """ Tests one server active in group who wishes to scale down
            but no healthy nodes in the load balancer.
            Desire to scale down should be denied and 0 should be returned
        """
        self.scaling_group.active_servers = ['server1']
        entity = fakes.FakeCloudMonitorEntity(info={'agent_id': 'server1'})

        entity = MagicMock(spec=CloudMonitorEntity)
        agent_id = PropertyMock(return_value='server1')
        type(entity).agent_id = agent_id

        check = MagicMock(spec=CloudMonitorCheck)
        check_type = PropertyMock(return_value='agent.plugin')
        type(check).type = check_type
        check.get_metric_data_points.return_value = [{'average': -1}]

        entity.list_checks.return_value = [check]
        mock_cloud_monitoring.list_entities.return_value = [entity]

        fake_lb = MagicMock(spec=CloudLoadBalancer)
        fake_clb.get.return_value = fake_lb

        raxmon_autoscale = Raxmon_autoscale(self.scaling_group)
        self.assertEquals(raxmon_autoscale.make_decision(), 0)

    def test_add_missing_check(self, mock_cloud_monitoring):
        """ Tests whether missing check is added. """

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

        mock_cloud_monitoring.list_entities.return_value = [entity]

        entity.create_check = MagicMock()
        raxmon_autoscale = Raxmon_autoscale(self.scaling_group)
        raxmon_autoscale.make_decision()

        entity.create_check.assert_called_once_with(check_type='agent.plugin',
                                                    target_alias='1.1.1.1',
                                                    period=30,
                                                    label='scale_me_agent.plugin',
                                                    details={},
                                                    timeout=15)
