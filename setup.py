#!/usr/bin/env python
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

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

from raxas.version import VERSION

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='rax-autoscaler',
    version=VERSION,
    url='https://github.com/boxidau/rax-autoscaler',
    author='''Simon Mirco, Simone Soldateschi, Suraj Thapa, Teddy Schmitz,
Jon Walton, Erik Ljungstrom''',
    author_email='''simon.mirco@rackspace.com,
simone.soldateschi@rackspace.co.uk, suraj.thapa@rackspace.com,
teddy.schmitz@rackspace.com, jon.walton@rackspace.com, erik.ljungstrom@rackspace.co.uk''',
    data_files=[('config', ['config/config-template.json',
                            'config/logging.conf']), ],
    description='Rackspace Auto Scale made easy',
    provides=['raxas.ext'],
    entry_points={
        "console_scripts": ['autoscale = raxas.autoscale:main',
                            'autoscale-config = raxas.autoscale_config:main'],
        "raxas.ext": ['raxmon = raxas.core_plugins.raxmon:Raxmon',
                      'raxmon_autoscale = raxas.core_plugins.raxmon_autoscale:Raxmon_autoscale',
                      'raxclb = raxas.core_plugins.raxclb:Raxclb',
                      'newrelic = raxas.core_plugins.newrelic:NewRelic']
    },
    keywords='rax rackspace autoscale scaling devops cloud openstack',
    maintainer='Simone Soldateschi',
    maintainer_email='simone.soldateschi@rackspace.co.uk',
    platforms='any',
    include_package_data=True,
    install_requires=required,
    license='Apache License, Version 2.0',
    long_description=open('README.txt').read(),
    packages=find_packages(),
    package_data={'docs': ['*.rst'], 'raxas': ['requirements.txt'], },
    # scripts=['raxas'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'Natural Language :: English'
    ],
)
