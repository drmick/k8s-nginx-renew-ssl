import time

from kubernetes import (
    client,
    config,
)


def cleanup(dns_key):
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    cmap = v1.read_namespaced_config_map(name='coredns', namespace='default')
    new_data = ''
    for i in cmap.data[dns_key].split('\n'):
        if not i.lstrip().startswith('_acme-challenge') and i:
            new_data += i + u'\n'
    cmap.data[dns_key] = new_data
    v1.replace_namespaced_config_map(name='coredns', namespace='default', body=cmap)


def restart_coredns(wait_time):
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    pods_list = v1.list_namespaced_pod(namespace='default')
    for i in pods_list.items:
        if i.metadata.labels.get('app') == 'coredns':
            v1.delete_namespaced_pod(name=i.metadata.name, namespace='default')
            time.sleep(wait_time)


def read_file(path):
    with open(path, 'r') as file:
        return file.read()
