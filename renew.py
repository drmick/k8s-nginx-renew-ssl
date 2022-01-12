import base64
import os
import shutil

import kubernetes
from certbot.main import main
from certs import dns_utils
from certs.configs import config


def generate_command_for_domain(domain, with_wildcard=False):
    domains = ['-d', domain]
    if with_wildcard:
        domains += ['-d', f'*.{domain}']

    return ['certonly',
            '--manual',
            '--preferred-challenges', 'dns',
            '--manual-auth-hook', './certs/auth.py',
            '--manual-cleanup-hook', './certs/cleanup.py',
            '--config-dir', './certs/ssl',
            '--logs-dir', './certs/ssl',
            '--work-dir', './certs/ssl',
            ] + domains + ['--preferred-challenges', 'dns-01',
                           '--server', 'https://acme-v02.api.letsencrypt.org/directory',
                           '--register-unsafely-without-email',
                           '--non-interactive',
                           '--agree-tos',
                           '--manual-public-ip-logging-ok'
                           ]


if __name__ == '__main__':
    kubernetes.config.load_incluster_config()
    v1 = kubernetes.client.CoreV1Api()
    if os.path.exists('./certs/ssl'):
        shutil.rmtree('./certs/ssl')
    for certificate_request in config['certificate_requests']:
        domain = certificate_request['domain']
        dns_key = certificate_request['dns_key']
        secret_name = certificate_request['secret_name']
        try:
            os.environ['CERTBOT_DNS_KEY'] = dns_key
            dns_utils.cleanup(dns_key)
            res = main(generate_command_for_domain(domain, with_wildcard=certificate_request['wildcard']))

            privkey = dns_utils.read_file(f'./certs/ssl/live/{domain}/privkey.pem')
            fullchain = dns_utils.read_file(f'./certs/ssl/live/{domain}/fullchain.pem')

            privkey = base64.b64encode(bytes(privkey, 'utf-8')).decode('utf-8')
            fullchain = base64.b64encode(bytes(fullchain, 'utf-8')).decode('utf-8')

            for namespace in certificate_request.get('namespaces'):
                secret_list = v1.list_namespaced_secret(namespace=namespace)
                for i in secret_list.items:
                    if i.metadata.name == secret_name:
                        v1.delete_namespaced_secret(namespace=namespace, name=secret_name)

                metadata = {'name': secret_name, 'namespace': namespace}
                data = {'tls.crt': fullchain, 'tls.key': privkey}
                api_version = 'v1'
                kind = 'Secret'
                body = kubernetes.client.V1Secret(api_version, data, kind, metadata, type='kubernetes.io/tls')
                api_response = v1.create_namespaced_secret(namespace, body)
        finally:
            del os.environ['CERTBOT_DNS_KEY']
            dns_utils.cleanup(dns_key)
