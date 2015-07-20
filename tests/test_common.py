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

import os
import sys
import json
from mock import patch, mock_open, MagicMock

from tests.base_test import BaseTest
from raxas import common
from raxas.autoscale import parse_args
from raxas.scaling_group import ScalingGroup


class CommonTest(BaseTest):
    @patch('os.path.isfile', return_value=True)
    @patch('os.access', return_value=True)
    def test_check_file_should_return_abs_path(self, access_mock, isfile_mock):
        check_file = '/config.cfg'

        self.assertEqual(common.check_file(check_file), check_file)
        isfile_mock.assert_called_once_with(check_file)
        access_mock.assert_called_once_with(check_file, os.R_OK)

    @patch('os.path.isfile', return_value=False)
    def test_check_file_should_return_none(self, isfile_mock):
        check_file = 'config.cfg'

        self.assertEqual(common.check_file(check_file), None)
        isfile_mock.assert_called_with('/etc/rax-autoscaler/config.cfg')

    def test_get_config_should_match(self):
        with patch('__builtin__.open',
                   mock_open(read_data=self._config_json)) as open_mock:

            self.assertEqual(common.get_config('config.cfg'),
                             json.loads(self._config_json))
            open_mock.assert_called_once_with('config.cfg')

    def test_get_config_should_return_none_with_invalid_json(self):
        with patch('__builtin__.open',
                   mock_open(read_data='trcfucbujnmk+')) as open_mock:

            self.assertEqual(common.get_config('config.cfg'), None)
            open_mock.assert_called_once_with('config.cfg')

    @patch('__builtin__.open')
    @patch('os.path.isfile', return_value=True)
    def test_read_uuid_cache(self, isfile_mock, open_mock):
        open_mock = mock_open(open_mock, read_data='0a6ebf42-d4ff-'
                                                   '4075-9425-ce50dda33955\n')
        file_handle = open_mock()
        file_handle.readline.return_value = '0a6ebf42-d4ff-' \
                                            '4075-9425-ce50dda33955\n'

        self.assertEqual(common.read_uuid_cache(), '0a6ebf42-d4ff-'
                                                   '4075-9425-ce50dda33955')

    @patch('os.path.isfile', return_value=False)
    def test_get_uuid_returns_none_when_missing_cache(self, isfile_mock):
        self.assertEqual(common.read_uuid_cache(), None)

    @patch('__builtin__.open')
    @patch('os.path.isfile', return_value=True)
    def test_get_uuid_returns_none_with_empty_cache(self, isfile_mock,
                                                    open_mock):
        open_mock = mock_open(open_mock)
        file_handle = open_mock()
        file_handle.readline.return_value = ''

        self.assertEqual(common.read_uuid_cache(), None)

    @patch('__builtin__.open')
    @patch('os.path.isfile', return_value=True)
    def test_get_uuid_returns_none_with_empty_datastore(self, isfile_mock,
                                                        open_mock):
        open_mock = mock_open(open_mock, read_data='iid-datasource-none\n')
        file_handle = open_mock()
        file_handle.readline.return_value = 'iid-datasource-none\n'

        self.assertEqual(common.read_uuid_cache(), None)

    @patch('sys.platform')
    def test_read_uuid_cache_returns_none_on_windows(self, platform_mock):
        platform_mock.startswith.return_value = 'win32'
        self.assertEqual(common.read_uuid_cache(), None)

        platform_mock.startswith.return_value = 'cygwin'
        self.assertEqual(common.read_uuid_cache(), None)

    @patch('__builtin__.open')
    def test_write_uuid_cache(self, open_mock):
        open_mock = mock_open(open_mock)
        common.write_uuid_cache('0a6ebf42-d4ff-4075-9425-ce50dda33955')

        file_handle = open_mock()
        self.assertEqual(file_handle.write.call_count, 1)
        file_handle.write.assert_called_once_with('0a6ebf42-d4ff-4075-9425-'
                                                  'ce50dda33955\n')

    @patch('raxas.common.read_uuid_cache', return_value='1234')
    def test_get_machine_uuid_from_cache(self, read_cache_mock):
        self.assertEqual(common.get_machine_uuid(None), '1234')

    @patch('raxas.common.read_uuid_cache', return_value=None)
    @patch('raxas.common.write_uuid_cache')
    @patch('netifaces.interfaces')
    @patch('netifaces.ifaddresses')
    @patch('pyrax.cloudservers')
    def test_get_machine_uuid(self, cloud_servers_mock,
                              ifaddr_mock, interfaces_mock, write_uuid_mock,
                              read_uuid_mock):

        uuid = 'eb8f2464-17a4-4796-a1ba-ab635ad287b9'
        scaling_group = MagicMock(spec=ScalingGroup)
        scaling_group.plugin_config = {'raxclb': {}}
        scaling_group.launch_config = {'load_balancers': [{'loadBalancerId': 231231}]}
        scaling_group.active_servers = [uuid]

        ifaddr_mock.return_value = {2: [{'addr': '119.9.94.249'}]}
        interfaces_mock.return_value = ['eth0']

        get_mock = cloud_servers_mock.servers.get.return_value
        get_mock.networks.values.return_value = \
            [['119.9.94.249', '2401:1800:7800:102:be76:4eff:fe1c:1945'],
             ['10.176.68.154']]
        get_mock.id = uuid

        self.assertEqual(common.get_machine_uuid(scaling_group), uuid)

    def test_get_user_value_from_config(self):
        sys.argv = ['/path/to/noserunner.py']
        args = parse_args()

        self.assertEqual(
            common.get_auth_value(args, json.loads(self._config_json),
                                  'os_username'), 'api_username')
        self.assertEqual(
            common.get_auth_value(args, json.loads(self._config_json),
                                  'os_password'), 'api_key')
        self.assertEqual(
            common.get_auth_value(args, json.loads(self._config_json),
                                  'os_region_name'), 'os_region_name')

        self.assertEqual(common.get_auth_value(args,
                                               json.loads(self._config_json),
                                               'should raise KeyError'),
                         None)

    def test_is_ipv4(self):
        self.assertEqual(common.is_ipv4('127.0.0.1'), True)
        self.assertEqual(common.is_ipv4('1.2.3.4'), True)
        self.assertEqual(common.is_ipv4('100.200.230.1'), True)
        self.assertEqual(common.is_ipv4('::1'), False)
        self.assertEqual(common.is_ipv4('100.200.300.400'), False)
        self.assertEqual(common.is_ipv4('hello'), False)
        self.assertEqual(common.is_ipv4('1.2.3.4.5'), False)
