Plugins
*******

Monitoring Plugins
==================

These plugins are used to provide different ways to determing whether to scale up or down.  Currently there are 2 monitoring plugins available.

Raxmon
------
Plugin for Rackspace monitoring.

Uses Rackspace cloud monitoring to check a server statstic and use it to make a scaling
decision.  The statistic is averaged over all currently active servers in the scaling group.
The plugin will create the check on the servers if it does not currently exist.  The Rackspace
monitoring agent must be installed on all servers in the scaling group and should be part of
your launch_configuration.


This is used to help smooth out fluctuations in the connection count so we do not scale on small
fluctuations.

Config should look like this:

.. code-block:: json

     "raxmon":{
         "scale_up_threshold": 0.6,
         "scale_down_threshold": 0.4,
         "check_config": {},
         "metric_name": "1m",
         "check_type": "agent.load_average",
         "max_samples": 10
     }

scale_up_threshold - Set this to a value that makes sense for the check you are performing.
If we go over this number we will scale up.

scale_down_threshold - Set this to a value that makes sense for the check you are performing.
If we go under this number we will scale down.

check_config (optional) - configuration options for the check we will be performing.  Used when
we are creating the check on servers that don't have it.

check_type - What type of check to perform.  Default is agent.load_average (check servers load
average)

metric_name - Name of metric checked.  We are checking the load_average over 1 minute periods
so the metric name could be 1m.  Default is 1m

max_samples - How many samples to pull from Rackspace monitoring, this helps limit the number
of API calls so you don't go over the daily limit.

Raxmon-autoscale
----------------
Plugin for Rackspace monitoring using an on-server plugin.

This plugin relies on the monitoring data from a Rackspace Monitoring plugin, which you can
find in the contrib/ directory. This should be placed in 
/usr/lib/rackspace-monitoring-agent/plugins/ and made executable on each server in the
autoscale group (through cloud-init, config management tools or already in an image).
This file runs local health checks (currently load average, number of active connections
and memory pct used), and reports its wish to either scale down, up or do
nothing based on its own health.
You should edit the threshold values near the top of the file to fit your particular workload.

This plugin collects the individual wishes of all servers, and makes a collective decision
by applying the following logic:
(assume three active servers)
One server wants to scale up = scale up (if a single node wants to do so, we disregard all others)
Two servers wants to scale down, one "do nothing" = do nothing
Three servers want to scale down = scale down  

Config should look like this:

.. code-block:: json

    "raxmon_autoscale":{
        "check_config": {"file": "autoscale.py"},
        "metric_name": "scale_me",
        "check_type": "agent.plugin",
        "load_balancers": [123456, 789101],
        "num_static_servers": 2,
        "max_samples": 10
    }

The load_balancers key is optional, and enables node health checking. This prevents the
scale-down action from being performed if the number of healthy nodes in any of the
specified load balancers is smaller than the number of active nodes in the scaling group.
This prevent instances where autoscale may inadvertently remove healthy
nodes and leaving only unhealthy ones.
If you have nodes under the same load balancer which aren't part of the
autoscale group, you set num_static_servers to this number. This will then be
taken into account when the calculation of number of healthy servers vs.
number of nodes in the AS group is done.
(if healthy_nodes_in_lb < (autoscale_node_cnt + static_servers))

Raxclb
------
Plugin for Rackspace cloud load balancer.


This checks the load balancer connection counts and uses it to make a scaling decision.
The algorithm is:

    (current_connection * 1.5 + historical_connection) / 2

This is used to help smooth out fluctuations in the connection count so we do not scale on small
fluctuations.

Config should look like this:

.. code-block:: json

    "raxclb":{
        "scale_up_threshold": 100,
        "scale_down_threshold": 10,
        "check_type": "SSL"
        "loadbalancers":[]
    }


scale_up_threshold - How many connections per server you want to handle.  We will multiply
this number by the number of servers currently active in the group.  If we go over this
number we will scale up.  Default is 50

scale_down_threshold - How many connections per server you want to handle.  We will multiply
this number by the number of servers currently active in the group.  If we go under this
number we will scale down.  Default is 1

check_type - set this to SSL if you want to check SSL connection counts instead of
regular http.  Default is to **not** check SSL.

loadbalancers - provide a list of loadbalancer ids to check.  If you do not provide
this we will detect the loadbalancer(s) in use by the scaling group and check all of them
and aggregate results.  Otherwise we will only check the loadbalancer ids you provide here.
Default is an empty list (Auto-detect loadbalancers).

New Relic
---------
Plugin for New Relic monitoring

Connects to New Relic monitoring API to view data and make a scaling decision based on that data.

Config should look like this:

.. code-block:: json

     "newrelic":{
         "api_key": "",
         "application_name":"<optional>",
         "scale_up_threshold": 0.6,
         "scale_down_threshold": 0.4,
         "metric_name": "System/Load",
         "metric_value": "average_value"
     }

api_key - this should be set to the your New Relic api key

scale_up_threshold - Set this to a value that makes sense for the check you are performing.
If we go over this number we will scale up.

scale_down_threshold - Set this to a value that makes sense for the check you are performing.
If we go under this number we will scale down.

metric_name - a valid New Relic metric name

metric_value - a valid New Relic metric value.

To see valid metric names and values please use the New Relic API explorer.
- For applications : https://rpm.newrelic.com/api/explore/applications/metric_names
- For Servers : https://rpm.newrelic.com/api/explore/servers/names

Creating Plugins
================

All monitoring plugins should inherit from raxas.core_plugins.base.  You must implement a make_decision
function that returns a 1 for scale up, -1, for scale down, or 0 for do nothing.::

    from raxas.core_plugins.base import PluginBase
    class Yourplugin(PluginBase):
        def __init__(self, scaling_group, config, args):
        super(Yourplugin, self).__init__(scaling_group, config, args)


