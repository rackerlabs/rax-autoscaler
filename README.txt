

RAX-AUTOSCALER


Uses the rackspace APIs to allow for scaling based on aggregate metrics
across a cluster.
Can be used and installed on the auto-scale group members or on a
dedicated management instance.

-   GitHub repository
-   PyPI package

[Stories in Ready] [Documentation Status] [Travis CI status]
[Coverage Status]


Installation

    pip install rax-autoscaler

Configuration

Read the Docs

What's New

V0.4 is here with a brand new plugin raxmon-autoscale, check it out in
the documentation above. Along for the ride are a host of improvements,
and fixes. Read the commit log if you have any questions and please
create an issue if you see any regressions.

Upgrading from 0.2

V0.3 is a major change from 0.2 and as such there are many breaking
changes in the configuration file.
Here is what you need to fix to upgrade successfully.

The monitoring information is now a plugin and needs to be moved to the
plugin section. The only monitoring plugin available in 0.2 was raxmon
so you should specify the raxmon plugin and just move the check_type,
check_config, metric_name, thresholds down.

Old Config

     "autoscale_groups": {
          "group0": {
              "group_id": "group id",
              "scale_up_policy": "scale up policy id",
              "scale_down_policy": "scale down policy id",
              "check_type": "agent.load_average",
              "check_config": {},
              "metric_name": "1m",
              "scale_up_threshold": 0.6,
              "scale_down_threshold": 0.4,
              "webhooks": {
                  "scale_up": {
                     "pre": [
                          "url",
                          "url"
                      ],
                     "post": [
                          "url"
                      ]
                  },
                  "scale_down": {
                      "pre": [
                          "url",
                          "url"
                       ],
                     "post": [
                        "url"
                      ]      
                  }
              }
          }
      }

New Config

        "autoscale_groups": {
            "group0": {
                "group_id": "704a2260-f4b9-46a9-be83-dbfb19919ee0",
                "scale_up_policy": "74588ebe-7ca7-4950-9b86-e622a11295b6",
                "scale_down_policy": "b22f4fce-132f-40af-b8c6-0e22704b1241",
                "webhooks": {
                    "scale_up": {
                        "pre": [
                            "url",
                            "url"
                        ],
                        "post": [
                            "url"
                        ]
                    },
                    "scale_down": {
                        "pre": [
                            "url",
                            "url"
                        ],
                        "post": [
                            "url"
                        ]
                    }
                },
                "plugins":{
                    "raxmon":{
                        "scale_up_threshold": 0.6,
                        "scale_down_threshold": 0.4,
                        "check_type": "agent.load_average",
                        "load_balancers": [17443]
                    }
                }
            }
        }


Contributing

-   Fork rax-autoscaler repository, and clone it on your laptop
-   Create _your feature_ branch from _devel_ branch:
    git checkout -b my-new-feature origin/devel
-   Commit, comment, push to your fork on GitHub, and create new _Pull
    Request_

Requirements

You might want to install pip packages in your Python virtualenv:

pip install -r requirements-dev.txt


License

    Copyright 2014 Rackspace US, Inc.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
