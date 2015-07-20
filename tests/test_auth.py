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

import unittest2
from mock import patch, mock_open
import pyrax
from pyrax.exceptions import AuthenticationFailed
from raxas.auth import Auth


class AuthTest(unittest2.TestCase):
    def __init__(self, *args, **kwargs):
        super(AuthTest, self).__init__(*args, **kwargs)
        self.username = "AUTHUSER"
        self.password = "AUTHPASS"
        self.api_key = "testtokenplsignore"
        self.region = "HKG"
        self.token_file = "/tmp/test.token"
        self.token_file_contents = """{"tenant_id": 123456,
        "token": "testtokenplsignore"}"""
        self.empty_json = """{"test":""}"""
        self.tenant_id = "123456"
        self.api_key = "testtokenplsignore"

    def test_load_token_true(self):
        auth = Auth(self.username, self.api_key, self.region)
        with patch('__builtin__.open',
                   mock_open(read_data=self.token_file_contents), create=True):
            self.assertTrue(auth.load_token())

    def test_load_token_nofile(self):
        auth = Auth(self.username, self.api_key, self.region)
        with patch('__builtin__.open', mock_open()):
            self.assertFalse(auth.load_token())

    def test_load_token_ioerror(self):
        auth = Auth(self.username, self.api_key, self.region)
        with patch('__builtin__.open', mock_open(
                read_data=self.token_file_contents)) as mocked_open:
            mocked_open.side_effect = IOError()
            self.assertFalse(auth.load_token())

    def test_load_token_wrong_keys(self):
        auth = Auth(self.username, self.api_key, self.region)
        with patch('__builtin__.open', mock_open(read_data=self.empty_json),
                   create=True):
            self.assertFalse(auth.load_token())

    def test_save_token(self):
        auth = Auth(self.username, self.api_key, self.region)
        auth._tenant_id = self.tenant_id
        auth._token = self.api_key
        auth._token_filename = "token.file"
        with patch('__builtin__.open', mock_open(), create=True) as mocked:
            self.assertTrue(auth.save_token())
            mocked.assert_called_once_with('token.file', 'w')

    @patch('pyrax.auth_with_token', return_value=True)
    def test_authenticate_token_success(self, mock_token):
        auth = Auth(self.username, self.api_key, self.region)
        auth._tenant_id = self.tenant_id
        auth._token = self.api_key
        auth._token_filename = "token.file"
        self.assertTrue(auth.authenticate_token())

    def test_authenticate_token_fail(self):
        auth = Auth(self.username, self.api_key, self.region)
        auth._tenant_id = self.tenant_id
        auth._token = self.api_key
        auth._token_filename = "token.file"
        with patch('pyrax.auth_with_token', return_value=True) as mocked:
            mocked.side_effect = pyrax.exceptions.AuthenticationFailed
            self.assertFalse(auth.authenticate_token())

    @patch('pyrax.identity', create=True)
    @patch('pyrax.set_credentials', return_value=True, create=True)
    def test_authenticate_creds_success(self, mock_creds, mock_auth):
        auth = Auth(self.username, self.api_key, self.region)

        self.assertTrue(auth.authenticate_credentials())

    @patch('pyrax.identity', create=True)
    @patch('pyrax.set_credentials', return_value=True, create=True)
    def test_authenticate_creds_false(self, mock_creds, mock_auth):
        auth = Auth(self.username, self.api_key, self.region)
        mock_creds.side_effect = pyrax.exceptions.AuthenticationFailed

        self.assertFalse(auth.authenticate_credentials())

    @patch.object(Auth, 'load_token', return_value=True)
    @patch.object(Auth, 'authenticate_token', return_value=True)
    def test_authenticate_token_flow(self, mock_auth, mock_load):
        auth = Auth(self.username, self.api_key, self.region)

        self.assertTrue(auth.authenticate())

    @patch.object(Auth, 'load_token', return_value=False)
    @patch.object(Auth, 'authenticate_credentials', return_value=True)
    def test_authenticate_cred_flow(self, mock_auth, mock_load):
        auth = Auth(self.username, self.api_key, self.region)

        self.assertTrue(auth.authenticate())

    @patch.object(Auth, 'load_token', return_value=False)
    @patch.object(Auth, 'authenticate_credentials', return_value=False)
    def test_authenticate_cred_fail(self, mock_auth, mock_load):
        auth = Auth(self.username, self.api_key, self.region)

        self.assertFalse(auth.authenticate())

    @patch.object(Auth, 'authenticate_credentials', return_value=False)
    @patch.object(Auth, 'load_token', return_value=True)
    @patch.object(Auth, 'authenticate_token', return_value=False)
    def test_authenticate_token_flow_fail(self, mock_auth, mock_load, mock_creds):
        auth = Auth(self.username, self.api_key, self.region)

        self.assertFalse(auth.authenticate())

    @patch('pyrax.auth_with_token', side_effect=AuthenticationFailed)
    @patch.object(Auth, 'authenticate_credentials', return_value=False)
    @patch.object(Auth, 'load_token', return_value=True)
    @patch.object(Auth, 'authenticate_token', return_value=False)
    def test_authenticate_token_exception(self, mock_auth, mock_load, mock_creds, mock_pyrax):
        auth = Auth(self.username, self.api_key, self.region)

        self.assertFalse(auth.authenticate())

    @patch('pyrax.identity', create=True)
    @patch.object(Auth, 'authenticate_token', return_value=False)
    def test_status(self, mock_auth, mock_identity):

        mock_identity.username = self.username
        mock_identity.api_key = self.api_key
        mock_identity.region = self.region
        mock_identity.token = self.token_file_contents
        mock_identity.tenant_id = self.tenant_id

        auth = Auth(self.username, self.api_key, self.region)
        status = auth.status()

        test_status = ('pyrax reports -- '
                       'username: {0:s}, apikey: {1:s}, '
                       'region: {2:s}, token: {3:s}, '
                       'tenant_id: {4:s}'
                       .format(self.username, self.api_key, self.region,
                               self.token_file_contents,
                               self.tenant_id))

        self.assertEqual(status, test_status)

    @patch('pyrax.identity', create=True)
    @patch('os.unlink')
    def test_unauthenticate_success(self, mock_os, mock_identity):
        auth = Auth(self.username, self.api_key, self.region)
        auth.force_unauthenticate()

        self.assertTrue(mock_identity.unauthenticate.called)
        self.assertTrue(mock_os.called)

    def test_tokenfilename(self):
        auth = Auth(self.username, self.api_key, self.region,
                    token_filename=self.token_file)
        self.assertEqual(auth.token_filename, self.token_file)

    @patch('pyrax.identity', create=True)
    @patch('os.unlink')
    def test_unauthenticate_pyrax_exc(self, mock_os, mock_identity):
        mock_identity.unauthenticate.side_effect = AttributeError
        auth = Auth(self.username, self.api_key, self.region)
        auth.force_unauthenticate()

        self.assertTrue(mock_identity.unauthenticate.called)
        self.assertTrue(mock_os.called)

    @patch('pyrax.identity', create=True)
    @patch('os.unlink')
    def test_unauthenticate_os_exc(self, mock_os, mock_identity):
        mock_os.side_effect = OSError
        auth = Auth(self.username, self.api_key, self.region)
        auth.force_unauthenticate()

        self.assertTrue(mock_identity.unauthenticate.called)
        self.assertTrue(mock_os.called)
