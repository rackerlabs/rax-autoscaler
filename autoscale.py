import common
import pyrax
import argparse
import netifaces
import time

def autoscale(group, config, cluster_mode):
  au = pyrax.autoscale
  cs = pyrax.cloudservers
  cm = pyrax.cloud_monitoring

  group_id = config.get(group, 'id')

  sgs = au.list()

  # Find scaling group from config
  for pos, sg in enumerate(sgs):
    if sg.id == group_id:
      break
  
  sg_state = sg.get_state()
  
  # Make sure there is atleast one instance in the AS group, if < 1 we cannot gauge the metrics of nothing
  if sg_state['active_capacity'] < 1:
    common.log('ERROR', '0 Servers present in scaling group invalid configuration, exiting')
    exit(1)

  common.log('INFO', 'Current active servers: ' + str(sg_state['active_capacity']))
  common.log('INFO', 'Cluster mode: ' + str(cluster_mode))

  # cluster mode is when this script runs on all instances
  # rather than relying on cooldown periods we elect 2 masters from the AS group
  if cluster_mode:
    # TODO use config drive to get UUID
    node_ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
    servers = cs.servers.list()
    node_id = None
  
    for server in servers:
      if server.networks['public'][0] == node_ip:
        node_id = server.id
        break
    
    masters = []

    if len(sg_state['active']) == 1:
      masters.push(sg_state['active'][0])
    elif len(sg_state['active']) > 1:
      masters.append(sg_state['active'][0])
      masters.append(sg_state['active'][1])
    else:
      common.log('ERROR', 'Unknown cluster state')
      exit(3)

    # For testing
    masters.append(node_id)

    if node_id is None:
      common.log('INFO', 'Could not find this server\'s node ID')
      common.log('ERROR', 'Cluster mode running on non-cluster member')
      exit(2)
    elif node_id in masters:
      common.log('INFO', 'Node is a master, continuing')
    else:
      common.log('INFO', 'Node is not a master, nothing to do. Exiting')
      exit(0)

  # Gather cluster statistics
  metric_sum = 0
  data_points = 0

  entities = cm.list_entities()
  for ent in entities:
    if ent.agent_id in sg_state['active']:  
      ent_checks = ent.list_checks()
      for check in ent_checks:
        if check.type == config.get(group, 'check_type', 'agent.cpu'):
          metrics = check.list_metrics()
          print metrics
          for metric in metrics:
            if metric.name == config.get(group, 'metric_name', 'usage_average'):
              data = check.get_metric_data_points(metric.name, int(time.time())-300, int(time.time()), points=2)
              if len(data) > 0:
                point = len(data)-1
                metric_sum += data[point]['average']
                data_points += 1

  if data_points == 0:
    common.log('ERROR', 'No data available')
    exit(4)
  else:
    average = metric_sum/data_points
    scale_up_threshold = config.getfloat(group, 'scale_up_threshold')
    scale_down_threshold = config.getfloat(group, 'scale_down_threshold')
   
    common.log('INFO', 'Metric at: ' + str(average))
    
    if average > scale_up_threshold:
      common.log('INFO', 'Above Threshold - Scaling Up')
      scale_policy = sg.get_policy(config.get(group, 'scale_up_policy'))
      scale_policy.execute()
    elif average < scale_down_threshold:
      common.log('INFO', 'Below Threshold - Scaling Down')
      scale_policy = sg.get_policy(config.get(group, 'scale_down_policy'))
      scale_policy.execute()
    else:
      common.log('INFO', 'Metric in target')

    print average

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--region', required=False,
    help='The region to build the servers',
    choices=['SYD', 'HKG', 'DFW', 'ORD', 'IAD', 'LON'],
    default=pyrax.default_region)
  parser.add_argument('--as-group', required=True,
    help='The autoscale group config ID')
  parser.add_argument('--cluster', required=False, default=False, action='store_true')

  args = vars(parser.parse_args())
  common.authenticate(args['region'])

  try:
    config = common.get_config(args['as_group'])
  except:
    common.log('ERROR', 'Unknown config section ' + args['as_group'])
  
  autoscale(args['as_group'], config, args['cluster'])
