Quick Start
***********

Installation
============
::

  pip install RAX-AutoScaler

Configuration
=============

Create ``config.json`` based on `config-template.json<https://github.com/rackerlabs/rax-autoscaler/blob/master/config/config-template.json>`, and edit the following:
* API username
* API key
* Region name
* Autoscaling group section should contain:
  * AutoScale Group UUID
  * Autoscale Scale Up Webhook Policy UUID
  * Autoscale Scale Down Webhook Policy UUID
  * Application webhook urls (Optional, can be removed if not using)
  * Plugins section
    * Name of plugin
    * Configuration directives specific to that plugin type

Usage
=====

Once configured you can invoke the autoscaler.py script.

--cluster option should be used when this script actually runs on auto-scale group members. Otherwise if it is running on a dedicated management instance you do not require this option.

--as-group option should be used when you have multiple groups listed in the config.json file.

--config-file option should be used if config.json file does not exists in current directory or in '/etc/rax-autoscaler' path.

Once tested you should configure this script to run as a cron job either on a management instance or on all cluster members

Cloud Init
==========

You can use the cloud-config file to auto-install RAX-Autoscaler on new servers.  For example to do so on Rackspace cloud using supernova
::

  supernova <region> boot --user-data ./cloud-config --image <image id/name> --flavor <flavor id/name> --config-drive=true <server name>

To use this with autoscale you would want to set the userdata of your launch configuration to the base64 encoded string of the file:

.. code-block:: json

  "launchConfiguration": {
        "args": {
            "server": {
                "config_drive" : true,
                "flavorRef": "general1-1",
                "imageRef": "CentOS 6.5 (PVHVM)",
                "key_name" : "MY_SSH_KEY",
                "user_data" : "I2Nsb3VkLWNvbmZpZwoKcGFja2FnZXM6CiAgLSBweXRob24tcGlwCgogIHJ1bmNtZDoKICAgIC0gWyBwaXAsIGluc3RhbGwsIFJBWC1BdXRvU2NhbGVyPT0wLjIuMjkgXQo=",
                "name": "test-autoscale"
            }
        },
        "type": "launch_server"
    }


This has been tested on these images:

- Ubuntu 14.04 LTS (PVHVM)
- CentOS 6.5 (PVHVM)

In the example the value of user_data contains the base64 encoded version of the following script:
::

  echo -n "I2Nsb3VkLWNvbmZpZwoKcGFja2FnZXM6CiAgLSBweXRob24tcGlwCgogIHJ1bmNtZDoKICAgIC0gWyBwaXAsIGluc3RhbGwsIFJBWC1BdXRvU2NhbGVyPT0wLjIuMjkgXQo=" | base64 -D

To base64 encode a script
::

    cat /path/to/USER_DATA | base64

Size of USER_DATA can be reduced with gzip:
::

    cat /path/to/USER_DATA | gzip | base64

If you are running autoscaler through cloud-init or any other automated system it is very important that you pin the version as newer versions may introduce breaking changes with previous versions.

config.json
===========

There are a few things to configure both on the Rackspace API side (essentially creating the autoscale group and setting the launch configuration) and on our side.

First up, create the autoscaling group in the portal and create 2 policies, 1 to scale up and another to scale down. The policy scale trigger should be set to webhook url.

The things we need now on the Rackspace side aren't available in the portal so you'll have to make use of https://cloud-api.info/ to quickly interact with the API. To login, you'll need your API key which is available from the portal under the "Account Settings" screen.

I'm going to quote the config/config-template.json file to make it easier to explain

.. code-block:: json

  "autoscale_groups": {
      "group0": {

"group0" is just a name used internally by autoscale.py to make it easier for the user to reference the scaling group. It can stay as group0 or be changed to match what you've called the group in the portal

.. code-block:: json

                    "group_id": "group id",

"group_id" is the UUID of the scaling group, this can be seen in the portal or in pitchfork by calling the "List Scaling Groups" API method https://cloud-api.info/autoscale/#list_scaling_groups-autoscale

.. code-block:: json

          "scale_up_policy": "scale up policy id",
          "scale_down_policy": "scale down policy id",

scale_up_policy and scale_down_policy requires the UUID of the policies configured as webhooks in the portal. You can retrieve the UUID in pitchfork by calling the Get Policies List method https://cloud-api.info/autoscale/#get_policies_list-autoscale


Webhook urls are an optional URL to call when we scale up or down. Pre is called before we call the Rackspace API, post is called after. You can configure multiple urls (or just a single url) to call at each stage.

Note
====
  RAX-AutoScaler depends on Rackspace Monitoring Agent to get the data from nodes in scaling group.

  If the agent is not installed please read: Install the Cloud Monitoring Agent: http://www.rackspace.com/knowledge_center/article/install-the-cloud-monitoring-agent


Contributing
============

- Fork it
- Create your feature branch (git checkout -b my-new-feature)
- Commit your changes (git commit -am 'Add some feature')
- Push to the branch (git push origin my-new-feature)
- Create new Pull Request
