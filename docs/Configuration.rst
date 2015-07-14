Advanced Configuration
**********************

Downloading from Cloud Files
============================

Rax-autoscaler comes with a utility to download a autoscaler configuration file from Rackspace cloud files.

::

    autoscale-config

You can either supply a file with the configuration options necessary to download this file or supply it all on the command line.

Arguments
=========

--container

The name of the container to download the configuration file from.

--os-username

Your cloud username

--os-password

Your cloud api-key

--config-file

The name of the file to download from the container specified, will also be saved as this file name on the host.

--config-directory

The directory that the config file will be downloaded to.

Example Usage
=============
::

    autoscale-config --container configurations --os-username mycloudusername --os-password myapikey  --config-file config.json --config-directory /etc/rax-autoscaler/

This will download a file named "config.json" from the configurations cloud files container to /etc/rax-autoscaler on the host.