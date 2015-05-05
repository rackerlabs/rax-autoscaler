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
#
# Example Config
#     "raxmon":{
#         "scale_up_threshold": 0.6,
#         "scale_down_threshold": 0.4,
#         "check_config": {},
#         "metric_name": "1m",
#         "check_type": "agent.load_average",
#         "max_samples": 10
#     }

import logging
import random
import time
import pyrax
from raxas.core_plugins.base import PluginBase


class Raxmon(PluginBase):
    """ Rackspace cloud monitoring plugin.

    """

    def __init__(self, scaling_group):
        super(Raxmon, self).__init__(scaling_group)

        config = scaling_group.plugin_config.get(self.name)

        self.scale_up_threshold = config.get('scale_up_threshold', 0.6)
        self.scale_down_threshold = config.get('scale_down_threshold', 0.4)
        self.check_config = config.get('check_config', {})
        self.metric_name = config.get('metric_name', '1m')
        self.check_type = config.get('check_type', 'agent.load_average')
        self.max_samples = config.get('max_samples', 10)
        self.scaling_group = scaling_group

    @property
    def name(self):
        return 'raxmon'

    def make_decision(self):
        """
        This function decides to scale up or scale down

        :returns: 1    scale up
                  0    do nothing
                 -1    scale down
                  None No data available
        """
        logger = logging.getLogger(__name__)

        results = []
        cm = pyrax.cloud_monitoring
        active_servers = self.scaling_group.active_servers

        entities = [entity for entity in cm.list_entities()
                    if entity.agent_id in active_servers]

        self.add_entity_checks(entities)

        logger.info('Gathering Monitoring Data')

        # Shuffle entities so the sample uses different servers
        entities = random.sample(entities, len(entities))

        for ent in entities:
            ent_checks = ent.list_checks()
            for check in ent_checks:
                if check.type == self.check_type:
                    data = check.get_metric_data_points(self.metric_name,
                                                        int(time.time())-600,
                                                        int(time.time()),
                                                        points=2)
                    if len(data) > 0:
                        point = len(data)-1
                        logger.info('Found metric for: %s, value: %s',
                                    ent.name, str(data[point]['average']))
                        results.append(float(data[point]['average']))
                        break

            # Restrict number of data points to save on API calls
            if len(results) >= self.max_samples:
                logger.info('max_samples value of %s reached, not gathering any more statistics',
                            self.max_samples)
                break

        if len(results) == 0:
            logger.error('No data available')
            return None
        else:
            average = sum(results)/len(results)

        logger.info('Cluster average for %s (%s) at: %s',
                    self.check_type, self.metric_name, str(average))

        if average > self.scale_up_threshold:
            logger.info("Raxmon reports scale up.")
            return 1
        elif average < self.scale_down_threshold:
            logger.info("Raxmon reports scale down.")
            return -1
        else:
            logger.info('Cluster within target parameters')
            return 0

    def add_entity_checks(self, entities):
        """This function ensures each entity has a cloud monitoring check.
           If the specific check in the json configuration data already exists, it will take
           no action on that entity

        """
        logger = logging.getLogger(__name__)

        logger.info('Ensuring monitoring checks exist')

        for entity in entities:
            check_exists = len([c for c in entity.list_checks()
                                if c.type == self.check_type])

            if not check_exists:
                ip_address = entity.ip_addresses.values()[0]
                logger.debug('server_id: %s, ip_address: %s', entity.agent_id, ip_address)
                entity.create_check(label='%s_%s' % (self.metric_name, self.check_type),
                                    check_type=self.check_type,
                                    details=self.check_config,
                                    period=60, timeout=30,
                                    target_alias=ip_address)
                logger.info('ADD - Cloud monitoring check (%s) to server with id: %s',
                            self.check_type, entity.agent_id)
            else:
                logger.info('SKIP - Cloud monitoring check (%s) already exists on server id: %s',
                            self.check_type, entity.agent_id)
