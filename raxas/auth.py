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

import json
import logging
import os.path
import pprint
import pyrax
import traceback


class Auth(object):
    """ This class implements Rackspace cloud account authentication

    """

    def __init__(self, username, apikey, region,
                 identity_type="rackspace",
                 token_filename=os.path.expanduser('~/.rax-autoscaler-token')):
        """ This method initializes the Auth class

            :param username: account user name
            :type name: str
            :param apikey: account api key
            :type name: str
            :param region: location
            :type name: str

        """
        logger = logging.getLogger(__name__)
        self._username = username
        self._apikey = apikey
        self._identity_type = identity_type
        self._region = region
        self._token_filename = token_filename
        self._token = None
        self._tenant_id = None
        logger.debug(self.__str__())

    def __str__(self, *args, **kwargs):
        """ This is used to generate logger debug messages

        """
        return ("username: %s, apikey: %s, identity_type: %s, "
                "region: %s, token_filename: %s, token: %s, "
                "tenant_id: %s" %
                (self._username, self._apikey, self._identity_type,
                 self._region, self._token_filename, self._token,
                 self._tenant_id))

    def status(self):
        """ This queries pyrax for values

            :returns: list -- the return value
        """
        pi = pyrax.identity
        return ("pyrax reports -- "
                "username: %s, apikey: %s, region: %s, token: %s, "
                "tenant_id: %s" %
                (pi.username, pi.api_key, pi.region, pi.token, pi.tenant_id))

    @property
    def token_filename(self):
        """ This returns token filename

            :returns: _token_filename
        """
        return self._token_filename

    def authenticate(self):
        """ This method loads a token from a file,
            authenticates with it, and if it fails then tries to authenticate
            with credentials

            :returns: True or False (Boolean)
        """
        logger = logging.getLogger(__name__)
        # try to authenticate with token
        if self.load_token():
            logger.debug("loaded token '%s' from file '%s'" %
                         (pprint.pformat(self._token), self._token_filename))
            if self.authenticate_token():
                logger.info('authenticated successfully')
                logger.debug("authenticated with token '%s' from file '%s'" %
                             (self._token, self._token_filename))
                return True
            else:
                logger.debug("cannot authenticate with token '%s' "
                             "from file '%s'"
                             % (self._token, self._token_filename))
        # try to authenticate with credentials
        if self.authenticate_credentials():
            logger.info('authenticated successfully')
            logger.debug("authenticated with credentials, username:%s,"
                         "api-key:%s, region:%s, identity_type:%s" %
                         (self._username, self._apikey, self._region,
                          self._identity_type))
            return True
        else:
            logger.debug("cannot authenticate with credentials, username:%s, "
                         "api-key:%s, region:%s, identity_type:%s" %
                         (self._username, self._apikey, self._region,
                          self._identity_type))
            return False

    def authenticate_credentials(self):
        """ This method tries to authenticate with available credentials

            :returns: True or False (Boolean)
        """
        logger = logging.getLogger(__name__)
        logger.debug('authenticating with credentials '
                     '(identity_type:%s, username:%s, api-key:%s, region=%s)'
                     % (self._identity_type, self._username, self._apikey,
                        self._region))
        try:
            pyrax.set_setting("identity_type", self._identity_type)
            pyrax.set_credentials(self._username, self._apikey,
                                  region=self._region)
            logger.info("authenticated with credentials, username:%s, "
                        "api-key:%s, region:%s, identity_type:%s" %
                        (self._username, self._apikey, self._region,
                         self._identity_type))
            logger.debug("user authenticated: %s"
                         % pyrax.identity.authenticated)
            if pyrax.identity.authenticated:
                self._token = pyrax.identity.auth_token
                self._tenant_id = pyrax.identity.tenant_id
                self.save_token()
            return pyrax.identity.authenticated
        except pyrax.exceptions.AuthenticationFailed:
            logger.warn("cannot authenticate with credentials")
            return False

    def authenticate_token(self):
        """ This authenticates with Rackspace cloud using existing token.

            :returns: True or False (Boolean)
        """
        logger = logging.getLogger(__name__)
        pyrax.set_setting('identity_type', self._identity_type)
        try:
            pyrax.auth_with_token(self._token, self._tenant_id,
                                  region=self._region)
            logging.info('authenticated with '
                         'token:%s, tenant_id:%s, region:%s' %
                         (self._token, self._tenant_id, self._region))
            return True
        except:
            logging.info('cannot authenticate with '
                         'token:%s, tenant_id:%s, region:%s' %
                         (self._token, self._tenant_id, self._region))
            logger.debug(traceback.format_exc())
            return False

    def force_unauthenticate(self):
        """ This unauthenticates and deletes token file

        """
        # unauthenticate
        try:
            pyrax.identity.unauthenticate()
        except AttributeError:
            pass
        # delete token file
        try:
            os.unlink(self._token_filename)
        except OSError:
            pass

    def load_token(self):
        """ This loads token from a file

            :returns: True or False (Boolean)
        """
        logger = logging.getLogger(__name__)
        try:
            with open(self._token_filename, 'r') as f:
                data = json.load(f)
            logger.debug("loaded data '%s' from file '%s'" %
                         (pprint.pformat(data), self._token_filename))
        except ValueError:
            logger.error("cannot decode JSON data in token file'%s'" %
                         self._token_filename)
            logger.debug(traceback.format_exc())
            return False
        except:
            logger.warning("cannot read token data from file '%s'" %
                           self._token_filename)
            logger.debug(traceback.format_exc())
            return False
        try:
            self._token = data['token']
            self._tenant_id = data['tenant_id']
            return True
        except KeyError:
            logger.error()
            logger.debug(traceback.format_exc())
            return False

    def save_token(self):
        """ This saves token into a file

            :returns: True or False (Boolean)
        """
        logger = logging.getLogger(__name__)
        data = {'token': self._token, 'tenant_id': self._tenant_id}
        try:
            with open(self._token_filename, 'w') as f:
                json.dump(data, f)
            return True
        except:
            logger.error("cannot write data '%s' to file '%s'" %
                         (pprint.pformat(data), self._token_filename))
            logger.debug(traceback.format_exc())
            return False
