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

import logging
import random
import time
import pyrax
import operator
from raxas.core_plugins.base import PluginBase


class Raxmon_autoscale(PluginBase):
    """ Rackspace cloud monitoring plugin.

    """

    def __init__(self, scaling_group):
        super(Raxmon_autoscale, self).__init__(scaling_group)

        config = scaling_group.plugin_config.get(self.name)

        self.scale_up_value = config.get('scale_up_value', 2)
        self.scale_down_value = config.get('scale_down_value', 1)
        self.do_nothing_value = config.get('do_nothing_value', 3)
        self.check_config = config.get('check_config', {})
        self.metric_name = config.get('metric_name', 'scale_me')
        self.check_type = config.get('check_type', 'agent.plugin')
        self.max_samples = config.get('max_samples', 10)
        self.lb = config.get('load_balancer', None)
        self.scaling_group = scaling_group

    @property
    def name(self):
        return 'raxmon_autoscale'

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
                                                        int(time.time())-300,
                                                        int(time.time()),
                                                        resolution='FULL')
                    if len(data) > 0:
                        point = len(data)-1
                        logger.info('Found metric for: %s, value: %s',
                                    ent.name, str(data[point]['average']))
                        results.append(data[point]['average'])
                        break

            # Restrict number of data points to save on API calls
            if len(results) >= self.max_samples:
                logger.info('max_samples value of %s reached, not gathering any more statistics',
                            self.max_samples)
                break

        num_results = len(results)
        scale_down = -1
        scale_up = 1
        do_nothing = 0
        scale_actions = { scale_down: 0, do_nothing: 0, scale_up: 0 }
        winner = 0
        if num_results == 0:
            logger.error('No data available')
            return None
        else:
            for result in results:
                if result not in scale_actions.keys():
                    logger.info("Duff data back from monitoring '%s' not a valid return" % result)
                    continue
                scale_actions[result] += 1
            if scale_actions.get(scale_up) > 0:
                logger.info("At least one node reports the wish to scale - scaling up...")
                return scale_up

            winner = max(scale_actions.iteritems(), key=operator.itemgetter(1))[0]
            logger.info("Collective decision: %s" % winner) 


        if winner == scale_down and self.lb:
            active_server_count = self.scaling_group.state['active_capacity']
            num_healthy_nodes = self.get_lb_status(self.lb)
            if num_healthy_nodes < active_server_count:
                logger.warning("Consensus was to scale down - but number of servers in scaling group (%s) exceeds the number of healthy nodes in the load balancer (%s). NOT scaling down!" % (active_server_count, num_healthy_nodes))
                winner = do_nothing

        return winner

    def get_lb_status(self, load_balancer):
        """ This function cehcks that the nodes behind a loadbalancer are healthy.
            This is in order to prevent scaling down when the nodes in an existing group
            are unhealthy
        """
        clb = pyrax.cloud_loadbalancers
        lb = clb.get(load_balancer)
        # If there are no nodes at all under an LB, the attribute 'nodes' doesn't exist at all
        try:
            nodes = lb.nodes
        except AttributeError as e:
            return 0

        num_healthy = 0
        for node in lb.nodes:
            if node.status == "ONLINE" and node.condition == "ENABLED":
                num_healthy += 1
        return num_healthy

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
                                    period=30, timeout=15,
                                    target_alias=ip_address)
                logger.info('ADD - Cloud monitoring check (%s) to server with id: %s',
                            self.check_type, entity.agent_id)
            else:
                logger.info('SKIP - Cloud monitoring check (%s) already exists on server id: %s',
                            self.check_type, entity.agent_id)
