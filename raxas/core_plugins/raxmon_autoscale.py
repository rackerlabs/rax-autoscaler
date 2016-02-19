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
# Config Example
#            "plugins":{
#                "raxmon_autoscale":{
#                    "check_config": {"file": "autoscale.py"},
#                    "metric_name": "scale_me",
#                    "check_type": "agent.plugin",
#                    "load_balancers": [123456, 789101],
#                    "num_static_servers": 2,
#                    "max_samples": 10
#                }
#            }
#
# The load_balancers key is optional, and enables node health checking. This prevents the
# scale-down action from being performed if the number of healthy nodes in any of the
# specified load balancers is less than the number of active nodes in the scaling group.
# This prevent instances where autoscale may inadvertently remove healthy
# nodes and leaving only unhealthy ones.
# If you have nodes under the same load balancer which aren't part of the
# autoscale group, you set num_static_servers to this number. This will then be
# taken into account when the calculation of number of healthy servers vs.
# number of nodes in the AS group is done.
# (if healthy_nodes_in_lb < (autoscale_node_cnt + static_servers))
#
# This plugin relies on the monitoring data from a Rackspace Monitoring plugin, which you can
# find in the contrib/ directory. This should be placed in
# /usr/lib/rackspace-monitoring-agent/plugins/ and made executable on each server in the
# autoscale group (through cloud-init, config management tools or already in an image).
# This file runs local health checks (currently load average, number of active connections
# and memory pct used), and reports its wish to either scale down, up or do nothing based
# on its own health.
# You should edit the threshold values near the top of the file to fit your particular workload.
#
# The code below collects the individual wishes of all servers, and makes a collective decision
# by applying some logic.
# For example:
# (assume three active servers)
# One server wants to scale up = scale up (if a single node wants to do so, we disregard all else)
# Two servers wants to scale down, one "do nothing" = do nothing
# Three servers want to scale down = scale down


import logging
import random
import time
import pyrax
import operator
from raxas.core_plugins.base import PluginBase
import raxas.monitoring as monitoring


class Raxmon_autoscale(PluginBase):

    """ Rackspace cloud monitoring plugin.

    """

    def __init__(self, scaling_group):
        super(Raxmon_autoscale, self).__init__(scaling_group)

        config = scaling_group.plugin_config.get(self.name)

        self.check_config = config.get('check_config', {})
        self.metric_name = config.get('metric_name', 'scale_me')
        self.check_type = config.get('check_type', 'agent.plugin')
        self.max_samples = config.get('max_samples', 10)
        self.num_static_servers = config.get('num_static_servers', 0)
        self.lbs = config.get('load_balancers', None)
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
        entities = monitoring.get_entities(self.scaling_group)

        monitoring.add_entity_checks(entities,
                                     self.check_type,
                                     self.metric_name,
                                     self.check_config)

        logger.info('Gathering Monitoring Data')

        # Shuffle entities so the sample uses different servers
        entities = random.sample(entities, len(entities))

        for ent in entities:
            ent_checks = ent.list_checks()
            for check in ent_checks:
                if check.type == self.check_type:
                    data = check.get_metric_data_points(self.metric_name,
                                                        int(time.time()) - 300,
                                                        int(time.time()),
                                                        resolution='FULL')
                    if len(data) > 0:
                        point = len(data) - 1
                        logger.info('Found metric for: %s, value: %s',
                                    ent.name, str(data[point]['average']))
                        results.append(data[point]['average'])
                        break

            # Restrict number of data points to save on API calls
            if len(results) >= self.max_samples:
                logger.info('max_samples value of %s reached, not gathering any more statistics',
                            self.max_samples)
                break

        scale_down = -1
        scale_up = 1
        do_nothing = 0
        scale_actions = {scale_down: 0, do_nothing: 0, scale_up: 0}
        winner = 0
        if not results:
            logger.error('No data available')
            return None

        for result in results:
            if result not in scale_actions.keys():
                logger.info(
                    "Duff data back from monitoring '%s' not a valid return" % result)
                continue
            scale_actions[result] += 1
        if scale_actions.get(scale_up) > 0:
            logger.info(
                "At least one node reports the wish to scale - scaling up...")
            return scale_up

        winner = max(
            scale_actions.iteritems(), key=operator.itemgetter(1))[0]
        logger.info("Collective decision: %s" % winner)

        if winner == scale_down and self.lbs:
            active_server_count = self.scaling_group.state['active_capacity']
            clb = pyrax.cloud_loadbalancers
            for load_balancer in self.lbs:
                num_healthy_nodes = self.get_lb_status(load_balancer, clb)
                if num_healthy_nodes < (
                        active_server_count + self.num_static_servers):
                    logger.warning("Consensus was to scale down - but number"
                                   " of servers in scaling group (%s) plus any"
                                   " static nodes exceeds the number"
                                   " of healthy nodes in load balancer %d (%s)."
                                   " NOT scaling down!" % (active_server_count,
                                                           load_balancer,
                                                           num_healthy_nodes))
                    winner = do_nothing

        return winner

    def get_lb_status(self, load_balancer, clb):
        """ This function cehcks that the nodes behind a loadbalancer are healthy.
            This is in order to prevent scaling down when the nodes in an existing group
            are unhealthy
        """
        lb = clb.get(load_balancer)
        # If there are no nodes at all under an LB, the attribute 'nodes'
        # doesn't exist at all
        try:
            nodes = lb.nodes
        except AttributeError as e:
            return 0

        num_healthy = 0
        for node in lb.nodes:
            if node.status == "ONLINE" and node.condition == "ENABLED":
                num_healthy += 1
        return num_healthy
