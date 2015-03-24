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

import argparse
import logging.config
import socket
from stevedore.named import NamedExtensionManager

from raxas import common
from raxas.enums import *
from raxas.colouredconsolehandler import ColouredConsoleHandler
from raxas.auth import Auth
from raxas.version import return_version
from raxas.scaling_group import ScalingGroup


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


def autoscale(group, config_data, args):
    """This function executes scale up or scale down policy

    :param group: group name
    :param config_data: json configuration data
    :param args: user provided arguments
    :returns: enums.ScaleEvent
    """
    try:
        group_config = config_data['autoscale_groups'][group]
    except KeyError:
        return common.exit_with_error('Unable to get scaling group config for group: %s', group)

    scaling_group = ScalingGroup(group_config, group)

    logger.info('Cluster Mode Enabled: %s', args.get('cluster', False))

    if args['cluster']:
        if scaling_group.is_master in [NodeStatus.Slave, NodeStatus.Unknown]:
            return ScaleEvent.NotMaster

    plugin_config = scaling_group.plugin_config
    mgr = NamedExtensionManager(
        namespace='raxas.ext',
        names=plugin_config.keys(),
        invoke_on_load=True,
        invoke_args=(scaling_group,)
        )
    logger.info('Loaded plugins: %s' % mgr.names())

    results = [result for result
               in mgr.map_method('make_decision')
               if result is not None]
    scaling_decision = sum(results)
    if scaling_decision <= -1:
        scaling_decision = -1
    elif scaling_decision >= 1:
        scaling_decision = 1

    scale = ScaleDirection(scaling_decision)
    if scale is ScaleDirection.Nothing:
        logger.info('Cluster within target parameters')
        return ScaleEvent.NoAction

    logger.info('Threshold reached - Scaling %s', scale.name)
    if not args['dry_run']:
        scaling_group.execute_webhook(scale, HookType.Pre)

        policy_result = scaling_group.execute_policy(scale)
        if policy_result == ScaleEvent.Success:
            scaling_group.execute_webhook(scale, HookType.Post)
            return ScaleEvent.Success
        elif policy_result == ScaleEvent.NoAction:
            return ScaleEvent.Success
        else:
            return ScaleEvent.Error
    else:
        logger.info('Scale %s prevented by --dry-run', scale.name)
        return ScaleEvent.Success


def parse_args():
    """This function validates user arguments and data in configuration file.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--as-group', required=False,
                        help='The autoscale group config ID')
    parser.add_argument('--os-username', required=False,
                        help='Rackspace Cloud user name')
    parser.add_argument('--os-password', required=False,
                        help='Rackspace Cloud account API key')
    parser.add_argument('--config-file', required=False, default='config.json',
                        help='The autoscale configuration .ini file'
                             '(default: config.json)'),
    parser.add_argument('--os-region-name', required=False,
                        help='The region to build the servers',
                        choices=['SYD', 'HKG', 'DFW', 'ORD', 'IAD', 'LON'])
    parser.add_argument('--cluster', required=False,
                        default=False, action='store_true')
    parser.add_argument('--version', action='version',
                        help='Show version number', version=return_version())
    parser.add_argument('--dry-run', required=False, default=False,
                        action='store_true',
                        help='Do not actually perform any scaling operations '
                             'or call webhooks')
    args = vars(parser.parse_args())

    return args


def main():
    """This function calls auth class for authentication and autoscale to
       execute scaling policy

    """
    args = parse_args()
    logger.info(return_version())
    for arg in args:
        logger.debug('argument provided by user ' + arg + ' : ' +
                     str(args[arg]))

    # CONFIG.ini
    config_file = common.check_file(args['config_file'])
    if config_file is None:
        common.exit_with_error('Either file is missing or is not readable: %s'
                               % args['config_file'])

    config_data = common.get_config(config_file)
    if config_data is None:
        common.exit_with_error('Failed to read config file: ' + config_file)

    as_group = args.get('as_group')
    if not as_group:
        if len(config_data['autoscale_groups'].keys()) == 1:
            as_group = config_data['autoscale_groups'].keys()[0]
        else:
            logger.debug("Getting system hostname")
            hostname = socket.gethostname()
            as_group = hostname.rsplit('-', 1)[0]

    username = common.get_auth_value(args, config_data, 'os_username')
    api_key = common.get_auth_value(args, config_data, 'os_password')
    region = common.get_auth_value(args, config_data, 'os_region_name')
    if None in (username, api_key, region):
        common.exit_with_error('Authentication credentials not set')
    region = region.upper()

    session = Auth(username, api_key, region)
    if not session.authenticate():
        common.exit_with_error('Authentication failed')

    scale_result = autoscale(as_group, config_data, args)
    if scale_result == ScaleEvent.Error:
        common.exit_with_error(None)
    else:
        log_name = None
        if hasattr(logger.root.handlers[0], 'baseFilename'):
            log_name = ': ' % logger.root.handlers[0].baseFilename
        logger.info('completed successfully %s', (log_name if log_name else ''))


if __name__ == '__main__':
    main()
