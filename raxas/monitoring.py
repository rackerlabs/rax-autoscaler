#!/usr/bin/env python
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

import logging
import pyrax


def get_entities(scaling_group):
    """ Returns a list of the cloud monitoring entities
        belonging to the active servers in a scaling group
    """
    cm = pyrax.cloud_monitoring
    active_servers = scaling_group.active_servers
    return [entity for entity in cm.list_entities()
            if entity.agent_id in active_servers]


def add_entity_checks(entities, check_type, metric_name, check_config=None,
                      period=30, timeout=15):
    """This function ensures each entity has a cloud monitoring check.
       If the specific check in the json configuration data already exists, it will take
       no action on that entity

    """
    logger = logging.getLogger()

    logger.info('Ensuring monitoring checks exist')

    for entity in entities:
        check_exists = len([c for c in entity.list_checks()
                            if c.type == check_type])

        if not check_exists:
            ip_address = entity.ip_addresses.values()[0]
            logger.debug(
                'server_id: %s, ip_address: %s', entity.agent_id, ip_address)
            entity.create_check(label='%s_%s' % (metric_name, check_type),
                                check_type=check_type,
                                details=check_config,
                                period=period, timeout=timeout,
                                target_alias=ip_address)
            logger.info('ADD - Cloud monitoring check (%s) to server with id: %s',
                        check_type, entity.agent_id)
        else:
            logger.info('SKIP - Cloud monitoring check (%s) already exists on server id: %s',
                        check_type, entity.agent_id)
