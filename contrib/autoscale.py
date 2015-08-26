#!/usr/bin/python

# This file goes into /usr/lib/rackspace-monitoring-agent/plugins/
# Remember to chmod +x

import os
import subprocess
from decimal import *

# Format of these (scale_down_threshold, scale_up_threshold) - anything in
# between results in a NOOP
load_average = (1.0, 2.0)
connections_port = 80
num_conns = (1, 50)
memory_pct = (15.0, 60.0)


# Internal variables - do not modify #
PROC_TCP = ["/proc/net/tcp", "/proc/net/tcp6"]


def read_tcp_connections():
    for proc_file in PROC_TCP:
        with open(proc_file, 'r') as f:
            content = f.readlines()
            content.pop(0)
    return content


def remove_empty_lines(arr):
    return [x for x in arr if x != '']


def _hex2dec(s):
    return str(int(s, 16))


def get_load_average():
    return os.getloadavg()[0]


def get_num_connections(port=80):
    ret = 0
    conns = read_tcp_connections()
    for conn in conns:
        line = remove_empty_lines(conn.split(" "))
        local_port = str(int(line[1].split(":")[1], 16))
        if line[3] == '01' and local_port == str(port):
            ret += 1

    return ret


scale_down = -1
scale_up = 1
do_nothing = 0

load_avg = 1
num_connections = 1
phys_mem = 3


def make_decision(load_avg, num_connections, phys_mem):
    # If everything is "do nothing" - we do nothing
    if all(var == do_nothing for var in (load_avg, num_connections, phys_mem)):
        return do_nothing
    # If one metric suggests we need to scale up - we scale up
    if any(var == scale_up for var in (load_avg, num_connections, phys_mem)):
        return scale_up
    # If all metrics say scale down, we scale down
    if all(var == scale_down for var in (load_avg, num_connections, phys_mem)):
        return scale_down

    return do_nothing


def get_phys_mem_pct():
    meminfo = dict((i.split()[0].rstrip(':'), int(i.split()[1]))
                   for i in open('/proc/meminfo').readlines())
    mem_free = meminfo.get(
        'MemFree') + meminfo.get('Buffers') + meminfo.get('Cached')
    getcontext().prec = 3
    return Decimal(((Decimal(meminfo.get('MemTotal')) / Decimal(mem_free)) - 1) * 100)


load_avg_scale = do_nothing
cur_load_average = get_load_average()
if load_average[0] < cur_load_average < load_average[1]:
    # Within the comfort zone - do nothing
    load_avg_scale = do_nothing
elif cur_load_average >= load_average[1]:
    # Above max - scale up
    load_avg_scale = scale_up
elif cur_load_average <= load_average[0]:
    # Below min - scale down
    load_avg_scale = scale_down

num_connections = get_num_connections(connections_port)
num_connections_scale = do_nothing
if num_conns[0] < num_connections < num_conns[1]:
    num_connections_scale = do_nothing
elif num_connections >= num_conns[1]:
    num_connections_scale = scale_up
elif num_connections <= num_conns[0]:
    num_connections_scale = scale_down

phys_mem_pct = get_phys_mem_pct()
phys_mem_scale = do_nothing
if memory_pct[0] < phys_mem_pct < memory_pct[1]:
    phys_mem_scale = do_nothing
elif phys_mem_pct >= memory_pct[1]:
    phys_mem_scale = scale_up
elif phys_mem_pct <= memory_pct[0]:
    phys_mem_scale = scale_down

scale = make_decision(load_avg_scale, num_connections_scale, phys_mem_scale)
print "metric scale_me int64", scale
