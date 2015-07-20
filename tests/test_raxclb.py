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

import unittest2

from mock import MagicMock, patch
from pyrax.exceptions import NotFound
from pyrax.cloudloadbalancers import CloudLoadBalancer

from raxas.core_plugins.raxclb import Raxclb
from raxas.scaling_group import ScalingGroup


@patch('pyrax.cloud_loadbalancers', create=True)
class RaxclbTest(unittest2.TestCase):
    def __init__(self, *args, **kwargs):
        super(RaxclbTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.scaling_group = MagicMock(spec=ScalingGroup)
        self.scaling_group.plugin_config = {'raxclb': {}}
        self.scaling_group.launch_config = {'load_balancers': [{'loadBalancerId': 231231}]}
        self.scaling_group.state = {'active_capacity': 1}

    def test_make_decision_no_lb(self, mock_clb):
        self.scaling_group.launch_config = {'test': 'case'}

        rclb = Raxclb(self.scaling_group)
        self.assertIsNone(rclb.make_decision())

    def test_make_decision_bad_lb(self, mock_clb):
        self.scaling_group.plugin_config = {'raxclb': {'loadbalancers': ['doesnotexist']}}
        mock_clb.get.side_effect = NotFound(404)

        rclb = Raxclb(self.scaling_group)
        self.assertIsNone(rclb.make_decision())

    def test_make_decision_scaleup(self, mock_clb):
        fakelb = MagicMock(spec=CloudLoadBalancer)
        fakelb.get_stats.return_value = {'currentConn': 100}
        mock_clb.get.return_value = fakelb

        rclb = Raxclb(self.scaling_group)
        self.assertEqual(1, rclb.make_decision())

    def test_make_decision_scaledown(self, mock_clb):
        fakelb = MagicMock(spec=CloudLoadBalancer)
        fakelb.get_stats.return_value = {'currentConn': 0}
        mock_clb.get.return_value = fakelb

        rclb = Raxclb(self.scaling_group)
        self.assertEqual(-1, rclb.make_decision())

    def test_make_decision_donothing(self, mock_clb):
        fakelb = MagicMock(spec=CloudLoadBalancer)
        fakelb.get_stats.return_value = {'currentConn': 20}
        mock_clb.get.return_value = fakelb

        rclb = Raxclb(self.scaling_group)
        self.assertEqual(0, rclb.make_decision())

    def test_make_decision_ssl(self, mock_clb):
        self.scaling_group.plugin_config = {'raxclb': {'check_type': 'ssl'}}
        fakelb = MagicMock(spec=CloudLoadBalancer)
        fakelb.get_stats.return_value = {'currentConnSsl': 20}
        fakelb.get_usage.return_value = {
            'loadBalancerUsageRecords': [
                {'averageNumConnectionsSsl': 5},
                {'averageNumConnectionsSsl': 8}
            ]
        }
        mock_clb.get.return_value = fakelb

        rclb = Raxclb(self.scaling_group)
        self.assertEqual(0, rclb.make_decision())
