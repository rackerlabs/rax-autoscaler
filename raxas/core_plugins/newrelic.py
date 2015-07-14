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
#
#             "plugins":{
#                 "newrelic":{
#                     "api_key": "",
#                     "application_name":"<optional>",
#                     "scale_up_threshold": 0.6,
#                     "scale_down_threshold": 0.4,
#                     "metric_name": "System/Load",
#                     "metric_value": "average_value"
#                 }
#
# To see valid metric names and values please use the API explorer.
# For applications : https://rpm.newrelic.com/api/explore/applications/metric_names
# For Servers : https://rpm.newrelic.com/api/explore/servers/names

import logging
from datetime import datetime as dt, timedelta
import pyrax
from raxas.core_plugins.base import PluginBase
try:
    from newrelic_api import Applications, Servers
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error('Please install newrelic-api.')
    exit(1)


class NewRelic(PluginBase):
    """ New Relic monitoring plugin.

    """

    def __init__(self, scaling_group):
        super(NewRelic, self).__init__(scaling_group)

        config = scaling_group.plugin_config.get(self.name)
        self.api_key = config.get('api_key', None)
        self.application_name = config.get('application', None)
        self.metric_name = config.get('metric_name', 'System/Load')
        self.metric_value = config.get('metric_value', 'average_value')
        self.time_period = config.get('time_period', 30)
        self.scale_up_threshold = config.get('scale_up_threshold', 0.6)
        self.scale_down_threshold = config.get('scale_down_threshold', 0.4)
        self.scaling_group = scaling_group

    @property
    def name(self):
        return 'newrelic'

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

        if self.application_name:
            a = Applications(self.api_key)
            app_list = a.list(filter_name=self.application_name)
            if app_list["applications"]:
                logger.info('Gathering Monitoring Data')
                app_id = app_list["applications"][0]["id"]
                then = dt.now() - timedelta(minutes=self.time_period)
                data = a.metric_data(app_id, [self.metric_name], values=[self.metric_value],
                                     summarize=True, from_dt=then, to_dt=dt.now())
                try:
                    value = (data["metric_data"]["metrics"][0]
                             ["timeslices"][0]["values"][self.metric_value])

                    if value > 0:
                            logger.info('Found metric for: %s, value: %s',
                                        self.metric_name, str(value))
                            results.append(float(value))
                except KeyError:
                    pass

        else:
            hostnames = []
            active_servers = self.scaling_group.active_servers
            for server_id in active_servers:
                server = pyrax.cloudservers.servers.get(server_id)
                hostnames.append(server.human_id)

            logger.info('Gathering Monitoring Data')

            s = Servers(self.api_key)
            for host in hostnames:
                relic_server = s.list(filter_name=host)

                if relic_server["servers"]:
                    id = relic_server["servers"][0]["id"]
                    then = dt.now() - timedelta(minutes=self.time_period)
                    data = s.metric_data(id, [self.metric_name],
                                         values=[self.metric_value], summarize=True,
                                         from_dt=then, to_dt=dt.now())
                    try:
                        value = (data["metric_data"]["metrics"][0]
                                 ["timeslices"][0]["values"][self.metric_value])

                        if value > 0:
                                logger.info('Found metric for: %s, value: %s',
                                            self.metric_name, str(value))
                                results.append(float(value))
                                break
                    except KeyError:
                        continue

        if len(results) == 0:
            logger.error('No data available')
            return None
        else:
            average = sum(results)/len(results)

        logger.info('Cluster average for %s (%s) at: %s',
                    self.metric_name, self.metric_value, str(average))

        if average > self.scale_up_threshold:
            logger.info("Raxmon reports scale up.")
            return 1
        elif average < self.scale_down_threshold:
            logger.info("Raxmon reports scale down.")
            return -1
        else:
            logger.info('Cluster within target parameters')
            return 0
