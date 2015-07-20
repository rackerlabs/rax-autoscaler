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
import unittest2
import json


class BaseTest(unittest2.TestCase):
    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)

        self._config_json = """
    {
        "auth": {
            "os_username": "api_username",
            "os_password": "api_key",
            "os_region_name": "os_region_name"
    },
    "autoscale_groups": {
        "group0": {
            "group_id": "group id",
            "scale_up_policy": "scale up policy id",
            "scale_down_policy": "scale down policy id",
            "webhooks": {
                "scale_up": {
                    "pre": [
                        "preup1",
                        "preup2"
                    ],
                    "post": [
                        "postup1"
                    ]
                },
                "scale_down": {
                    "pre": [
                        "predwn1",
                        "predwn2"
                    ],
                    "post": [
                        "postdwn1"
                    ]
                }
            },
            "plugins":{
                "raxmon":{
                    "scale_up_threshold": 0.6,
                    "scale_down_threshold": 0.4,
                    "check_config": {},
                    "metric_name": "1m",
                    "check_type": "agent.load_average"
                        }
                    }
                }
            }
        }
        """

        self._config_parsed = json.loads(self._config_json)
