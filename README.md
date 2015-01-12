# RAX-AutoScaler

Uses the rackspace APIs to allow for scaling based on aggregate metrics across a cluster.
Can be used and installed on the auto-scale group members or on a dedicated management instance.

- [GitHub repository](https://github.com/rackerlabs/rax-autoscaler)
- [PyPI package](https://pypi.python.org/pypi/rax-autoscaler)

[![Stories in Ready](https://badge.waffle.io/boxidau/rax-autoscaler.svg?label=ready&title=Ready)](http://waffle.io/boxidau/rax-autoscaler) [![Documentation Status](https://readthedocs.org/projects/rax-autoscaler/badge/?version=latest)](https://readthedocs.org/projects/rax-autoscaler/) [![Travis CI status](https://travis-ci.org/boxidau/rax-autoscaler.svg)](https://travis-ci.org/boxidau/rax-autoscaler/builds)
[![Coverage Status](https://coveralls.io/repos/boxidau/rax-autoscaler/badge.png?branch=devel)](https://coveralls.io/r/boxidau/rax-autoscaler?branch=devel)

## Installation

```
pip install rax-autoscaler
```

### Configuration
Create ```config.json``` based on [config-template.json](https://github.com/boxidau/rax-autoscaler/blob/devel/config/config-template.json), and edit the following:
- API username
- API key
- Region name
- Autoscaling group section should contain:
  - AutoScale Group UUID
  - Scale Up Policy UUID
  - Scale Down Policy UUID
  - Check Type (agent.cpu, agent.load_average...)
  - Metric Name (depends on the check type)
  - Scale Up Threshold
  - Scale Down Threshold
  - Webhooks Url (Pre & Post commit url(s) for scale up/down)

## Usage
Once configured you can invoke the autoscaler.py script.

--cluster option should be used when this script actually runs on auto-scale group members. Otherwise if it is running on a dedicated management instance you do not require this option.

--as-group option should be used when you have multiple groups listed in the config.json file.

--config-file option should be used if config.json file does not exists in current directory or in '/etc/rax-autoscaler' path.

Once tested you should configure this script to run as a cron job either on a management instance or on all cluster members

##Cloud Init
You can use the cloud-config file to auto-install RAX-Autoscaler on new servers.  For example to do so on Rackspace cloud using supernova

```
supernova <region> boot --user-data ./cloud-config --image <image id/name> --flavor <flavor id/name> --config-drive=true <server name>
```

To use this with autoscale you would want to set the userdata of your launch configuration to the base64 encoded string of the file:


```
"launchConfiguration": {
        "args": {
            "server": {
                "config_drive" : true,
                "flavorRef": "general1-1",
                "imageRef": "CentOS 6.5 (PVHVM)",
                "key_name" : "MY_SSH_KEY",
                "user_data" : "I2Nsb3VkLWNvbmZpZwoKcGFja2FnZXM6CiAgLSBweXRob24tcGlwCgpydW5jbWQ6CiAgLSBbIHBpcCwgaW5zdGFsbCwgcmF4LWF1dG9zY2FsZXIgXQo=",
                "name": "test-autoscale"
            }
        },
        "type": "launch_server"
    }
```

This has been tested on these images:

- Ubuntu 14.04 LTS (PVHVM)
- CentOS 6.5 (PVHVM)

In the example the value of ```user_data``` contains the base64 encoded version of the following script:

```
$ echo -n "I2Nsb3VkLWNvbmZpZwoKcGFja2FnZXM6CiAgLSBweXRob24tcGlwCgpydW5jbWQ6CiAgLSBbIHBpcCwgaW5zdGFsbCwgUkFYLUF1dG9TY2FsZXIgXQo=" | base64 -D
#cloud-config

packages:
- python-pip

runcmd:
- [ pip, install, RAX-AutoScaler ]
```

FYI - To base64 encode a script:

```
cat /path/to/USER_DATA | base64
```

Size of ```USER_DATA``` can be reduced with gzip:

```
cat /path/to/USER_DATA | gzip | base64
```

### Note

RAX-AutoScaler depends on Rackspace Monitoring Agent to get the data from nodes in scaling group.
If the agent is not installed please read: [Install the Cloud Monitoring Agent](http://www.rackspace.com/knowledge_center/article/install-the-cloud-monitoring-agent)

## Contributing

- Fork [rax-autoscaler](https://github.com/boxidau/rax-autoscaler) repository, and clone it on your laptop
- Create *your feature* branch from *devel* branch: ```git checkout -b my-new-feature origin/devel```
- Commit, comment, push to your fork on [GitHub](https://github.com), and create new *Pull Request*

### Requirements

You might want to install pip packages in your Python virtualenv:

```pip install -r requirements-dev.txt```

## License

```
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
```
