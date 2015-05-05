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
from raxas.scaling_group import ScalingGroup
from raxas.core_plugins.newrelic import NewRelic
from novaclient.v1_1.servers import Server
from newrelic_api import Applications, Servers


class NewRelicTest(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(NewRelicTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.scaling_group = MagicMock(spec=ScalingGroup)
        self.scaling_group.plugin_config = {'newrelic': {}}
        self.scaling_group.state = {'active_capacity': 1}

    @patch('raxas.core_plugins.newrelic.Applications', create=True)
    def test_scaleup_application(self, mock_newrelic_api):
        self.scaling_group.plugin_config = {'newrelic': {
            "api_key": "fakeapikey",
            "application": "Test",
            "metric_name": "Agent/MetricsReported/count",
            "metric_value": "average_response_time"}}
        mock_application = MagicMock(spec=Applications)
        mock_newrelic_api.return_value = mock_application
        mock_application.list.return_value = {"applications": [{"name": "Test", "id": 123456}]}
        mock_application.metric_data.return_value = {"metric_data": {
            "metrics": [{"timeslices": [{"values": {"average_response_time": 15}}]}]}}
        newrelic = NewRelic(self.scaling_group)
        self.assertEqual(1, newrelic.make_decision())

    @patch('pyrax.cloudservers', create=True)
    @patch('raxas.core_plugins.newrelic.Servers', create=True)
    def test_scaleup_servers(self, mock_newrelic_api, mock_pyrax):
        self.scaling_group.plugin_config = {'newrelic': {
            "api_key": "fakeapikey",
            "metric_name": "Agent/MetricsReported/count",
            "metric_value": "average_response_time"}}
        self.scaling_group.active_servers = [123456]
        mock_nova_server = MagicMock(spec=Server)
        mock_nova_server.human_id.return_value = "Test-server"
        mock_server = MagicMock(spec=Servers)
        mock_pyrax.servers.get.return_value = mock_nova_server
        mock_server.list.return_value = {"servers": [{"name": "Test-server", "id": 512354134}]}
        mock_server.metric_data.return_value = {"metric_data": {
            "metrics": [{"timeslices": [{"values": {"average_response_time": 15}}]}]}}
        mock_newrelic_api.return_value = mock_server
        newrelic = NewRelic(self.scaling_group)
        self.assertEqual(1, newrelic.make_decision())

    @patch('raxas.core_plugins.newrelic.Applications', create=True)
    def test_no_results(self, mock_newrelic_api):
        self.scaling_group.plugin_config = {'newrelic': {
            "application": "Test",
            "api_key": "fakeapikey",
            "metric_name": "Agent/MetricsReported/count",
            "metric_value": "average_response_time"}}

        mock_application = MagicMock(spec=Applications)
        mock_newrelic_api.return_value = mock_application
        mock_application.list.return_value = {"applications": [{"name": "Test", "id": 123456}]}
        mock_application.metric_data.return_value = {}
        newrelic = NewRelic(self.scaling_group)
        self.assertIsNone(newrelic.make_decision())

    @patch('pyrax.cloudservers', create=True)
    @patch('raxas.core_plugins.newrelic.Servers', create=True)
    def test_key_error(self, mock_newrelic_api, mock_pyrax):
        self.scaling_group.plugin_config = {'newrelic': {
            "api_key": "fakeapikey",
            "metric_name": "Agent/MetricsReported/count",
            "metric_value": "average_response_time"}}

        self.scaling_group.active_servers = [123456]
        mock_nova_server = MagicMock(spec=Server)
        mock_nova_server.human_id.return_value = "Test-server"
        mock_server = MagicMock(spec=Servers)
        mock_pyrax.servers.get.return_value = mock_nova_server
        mock_server.list.return_value = {"servers": [{"name": "Test-server", "id": 512354134}]}
        mock_server.metric_data.return_value = {}
        mock_newrelic_api.return_value = mock_server
        newrelic = NewRelic(self.scaling_group)
        self.assertIsNone(newrelic.make_decision())

    @patch('raxas.core_plugins.newrelic.Applications', create=True)
    def test_scaledown_application(self, mock_newrelic_api):
        self.scaling_group.plugin_config = {'newrelic': {
            "api_key": "fakeapikey",
            "application": "Test",
            "metric_name": "Agent/MetricsReported/count",
            "scale_down_threshold": 10,
            "scale_up_threshold": 15,
            "metric_value": "average_response_time"}}
        mock_application = MagicMock(spec=Applications)
        mock_newrelic_api.return_value = mock_application
        mock_application.list.return_value = {"applications": [{"name": "Test", "id": 123456}]}
        mock_application.metric_data.return_value = {"metric_data": {
            "metrics": [{"timeslices": [{"values": {"average_response_time": 5}}]}]}}
        newrelic = NewRelic(self.scaling_group)
        self.assertEqual(-1, newrelic.make_decision())

    @patch('raxas.core_plugins.newrelic.Applications', create=True)
    def test_do_nothing_application(self, mock_newrelic_api):
        self.scaling_group.plugin_config = {'newrelic': {
            "api_key": "fakeapikey",
            "application": "Test",
            "metric_name": "Agent/MetricsReported/count",
            "scale_down_threshold": 10,
            "scale_up_threshold": 15,
            "metric_value": "average_response_time"}}
        mock_application = MagicMock(spec=Applications)
        mock_newrelic_api.return_value = mock_application
        mock_application.list.return_value = {"applications": [{"name": "Test", "id": 123456}]}
        mock_application.metric_data.return_value = {"metric_data": {
            "metrics": [{"timeslices": [{"values": {"average_response_time": 12}}]}]}}
        newrelic = NewRelic(self.scaling_group)
        self.assertEqual(0, newrelic.make_decision())
