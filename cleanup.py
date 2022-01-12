#!/usr/bin/python

import os

from certs.dns_utils import cleanup

if __name__ == '__main__':
    dns_key = os.environ['CERTBOT_DNS_KEY']
    cleanup(dns_key)
