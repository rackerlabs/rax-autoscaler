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

import pyrax
import argparse
from pyrax.exceptions import NoSuchContainer, NoSuchObject
import logging.config
from raxas import common
from raxas.colouredconsolehandler import ColouredConsoleHandler
from raxas.auth import Auth
from raxas.version import return_version

# CHECK logging.conf
logging_config = common.check_file('logging.conf')

if logging_config is None:
    logging.handlers.ColouredConsoleHandler = ColouredConsoleHandler
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

else:

    logging_conf_file = logging_config
    logging.handlers.ColouredConsoleHandler = ColouredConsoleHandler
    logging.config.fileConfig(logging_conf_file)
    logger = logging.getLogger(__name__)


def parse_args():
    """This function validates user arguments and data in configuration file.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--container', required=False,
                        help='The container that the '
                             'config file is stored in.')
    parser.add_argument('--os-username', required=False,
                        help='Rackspace Cloud user name')
    parser.add_argument('--os-password', required=False,
                        help='Rackspace Cloud account API key')
    parser.add_argument('--config-file', required=False, default='config.json',
                        help='The name of the configuration file.'
                             '(default: config.json)')
    parser.add_argument('--os-region-name', required=False,
                        help='The region the container is in.',
                        choices=['SYD', 'HKG', 'DFW', 'ORD', 'IAD', 'LON'])
    parser.add_argument('--config-directory', required=False,
                        default='/etc/rax-autoscaler/',
                        help='Directory to save/read config file')

    args = vars(parser.parse_args())

    return args


def download_config_private(config_data, args):
    """This function downloads the autoscale
    configuration file from a private cloud files container.

    :param config_data: json configuration data
    :param args: passed in arguments

    """

    cf = pyrax.cloudfiles

    container_name = common.get_auth_value(args, config_data, 'container')
    file_name = args['config_file']
    file_directory = args['config_directory']

    if container_name is None:
        common.exit_with_error('No container name defined')

    try:
        container = cf.get_container(container_name)
        container.download(file_name, file_directory, structure=False)
    except NoSuchContainer:
        common.exit_with_error('Invalid container name')
    except NoSuchObject:
        common.exit_with_error('Config file %s does not exist' % file_name)

    return None


def main():
    """This function calls auth class for authentication and then calls a function
    downloads the config file

    """
    args = parse_args()

    # CONFIG.ini
    config_file = common.check_file(args['config_file'])
    if config_file is None:
        logger.info('No config file found, '
                    'checking to see if we have credentials.')
        if args['os_username'] is None and args['os_password'] is None:
            common.exit_with_error("If there is no config file you "
                                   "must specify a username and password.")
    # Show Version
    logger.info(return_version())

    for arg in args:
        logger.debug('argument provided by user ' + arg + ' : ' +
                     str(args[arg]))

    config_data = common.get_config(config_file)

    username = common.get_auth_value(args, config_data, 'os_username')
    if username is None:
        common.exit_with_error('No os_username defined.')
    api_key = common.get_auth_value(args, config_data, 'os_password')
    if api_key is None:
        common.exit_with_error('No os_password defined.')
    region = common.get_auth_value(args, config_data, 'os_region_name')
    if region is None:
        common.exit_with_error('No os_region_name defined.')

    session = Auth(username, api_key, region)

    if session.authenticate() is True:
        download_config_private(config_data, args)
        log_file = None
        if hasattr(logger.root.handlers[0], 'baseFilename'):
            log_file = logger.root.handlers[0].baseFilename
        if log_file is None:
            logger.info('completed successfully')
        else:
            logger.info('completed successfully: %s', log_file)
    else:
        common.exit_with_error('Authentication failed')

if __name__ == '__main__':
    main()
