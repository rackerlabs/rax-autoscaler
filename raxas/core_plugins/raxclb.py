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
# Example config:
#
#     "raxclb":{
#         "scale_up_threshold": 50,
#         "scale_down_threshold": 1,
#         "check_type": "",
#         "load_balancers": <optional>
#     }

import pyrax
from raxas.core_plugins.base import PluginBase
from datetime import datetime, timedelta
import logging
from pyrax.exceptions import NotFound


class Raxclb(PluginBase):
    """ Rackspace cloud load balancer plugin.

    """

    def __init__(self, scaling_group):
        super(Raxclb, self).__init__(scaling_group)

        self.scaling_group = scaling_group
        config = scaling_group.plugin_config.get(self.name)

        self.scale_up_threshold = config.get('scale_up_threshold', 50)
        self.scale_down_threshold = config.get('scale_down_threshold', 1)
        self.check_type = config.get('check_type', '')
        self.lb_ids = config.get('loadbalancers', [])
        self.check_time = 2
        self.scaling_group = scaling_group

    @property
    def name(self):
        return 'raxclb'

    def make_decision(self):
        """
        This function decides to scale up or scale down

        :returns: 1    scale up
                  0    do nothing
                 -1    scale down
                  None No data available
        """

        logger = logging.getLogger(__name__)

        clb = pyrax.cloud_loadbalancers

        if not self.lb_ids:
            launch_config = self.scaling_group.launch_config
            if launch_config is None:
                return None

            try:
                self.lb_ids = [lb.get('loadBalancerId') for lb
                               in launch_config.get('load_balancers')]
            except TypeError:
                logger.error('No loadbalancer found, please either define a '
                             'loadbalancer to check or add one to the scaling group.')
                return None

        start_time = datetime.utcnow() - timedelta(hours=int(self.check_time))

        results = []

        active_server_count = self.scaling_group.state['active_capacity']

        self.scale_up_threshold = self.scale_up_threshold * active_server_count
        self.scale_down_threshold = self.scale_down_threshold * active_server_count

        if self.check_type.upper() == 'SSL':
            hist_check = 'averageNumConnectionsSsl'
            cur_check = 'currentConnSsl'

        else:
            hist_check = 'averageNumConnections'
            cur_check = 'currentConn'

        for lb in self.lb_ids:
            try:
                check_clb = clb.get(lb)
            except NotFound:
                logger.error('Loadbalancer specified does not exist')
                return None

            usage = check_clb.get_usage(start=start_time)
            current_usage = check_clb.get_stats()

            records = []

            for record in usage.get('loadBalancerUsageRecords'):
                records.append(record.get(hist_check))

            try:
                current_conn = current_usage.get(cur_check)
                average_historical = sum(records) / len(records)
                average = ((current_conn * 1.5) + average_historical) / 2
            except ZeroDivisionError:
                average = current_usage.get(cur_check)

            if average > self.scale_up_threshold:
                results.append(1)
                logger.info("Raxclb reports scale up for lb %s", lb)
            elif average < self.scale_down_threshold:
                results.append(-1)
                logger.info("Raxclb reports scale down for lb %s", lb)
            else:
                results.append(0)
                logger.info("Raxclb reports normal for lb %s", lb)

        return sum(results)
