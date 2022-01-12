#!/usr/bin/python
import os

from certs import dns_utils
from kubernetes import (
    client,
    config,
)

if __name__ == '__main__':
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    cmap = v1.read_namespaced_config_map(name='coredns', namespace='infra')
    domain = os.environ['CERTBOT_DOMAIN']
    dns_key = os.environ['CERTBOT_DNS_KEY']
    validation_code = os.environ['CERTBOT_VALIDATION']
    domain_data = cmap.data[dns_key]
    domain_data += f'_acme-challenge.{domain}.          300   IN TXT        {validation_code}\n'
    cmap.data[dns_key] = domain_data
    v1.replace_namespaced_config_map(name='coredns', namespace='default', body=cmap)

    dns_utils.restart_coredns(20)
