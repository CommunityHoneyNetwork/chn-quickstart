#!/usr/bin/env python3
import sys
import argparse
import validators
import secrets
import string
import os


def generate_password(length=32):

    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password


def check_url(url):
    """
    Make sure this is a real URL
    """
    if validators.url(url):
        return url
    else:
        raise argparse.ArgumentTypeError("%s is an invalid url" % url)


def parse_args():

    certificate_strategies = [
        'CERTBOT',
        'BYO',
        'SELFSIGNED'
    ]
    parser = argparse.ArgumentParser(
        description='Generate chnserver.sysconfig using some sane defaults')
    parser.add_argument(
        '-s', '--server-base-url', help='Public URL for your CHN Server',
        required=True, type=check_url)
    parser.add_argument(
        '-c', '--certificate-strategy',
        default='CERTBOT', choices=certificate_strategies,
        help='Certificate strategy for TLS'
    )
    parser.add_argument(
        '-o', '--output-file', required=True,
        help='File path to write out to'
    )
    parser.add_argument(
        '-f', '--force-overwrite', action='store_true',
        help='Forcibly overwrite file, even if it exists'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    chnserver_template = """# Generated from generate_chn_sysconfig.py
# This file is read from /etc/sysconfig/chnserver or /etc/default/chnserver
# depending on the base distro
#
# This can be modified to change the default setup of the chnserver unattended
installation

DEBUG=false

EMAIL=admin@localhost
# For TLS support, you MUST set SERVER_BASE_URL to "https://your.site.tld"
SERVER_BASE_URL='{server_base_url}'
HONEYMAP_URL=''
REDIS_URL='redis://redis:6379'
MAIL_SERVER='127.0.0.1'
MAIL_PORT=25
MAIL_TLS='y'
MAIL_SSL='y'
MAIL_USERNAME=''
MAIL_PASSWORD=''
DEFAULT_MAIL_SENDER=''
MONGODB_HOST='mongodb'
MONGODB_PORT=27017
HPFEEDS_HOST='hpfeeds'
HPFEEDS_PORT=10000

SUPERUSER_EMAIL='admin@localhost'
SUPERUSER_PASSWORD='{password}'
SECRET_KEY=''
DEPLOY_KEY=''

# See https://communityhoneynetwork.readthedocs.io/en/stable/certificates/
# Options are: 'CERTBOT', 'SELFSIGNED', 'BYO'
CERTIFICATE_STRATEGY='{certificate_strategy}'
""".format(
        server_base_url=args.server_base_url,
        password=generate_password(),
        certificate_strategy=args.certificate_strategy
    )

    if not os.path.exists(args.output_file) or args.force_overwrite:
        f = open(args.output_file, 'w')
        f.write(chnserver_template)
        f.close()
        print("Wrote file to %s" % args.output_file)
    else:
        sys.stderr.write("Not writing file, add -f to override\n")


if __name__ == "__main__":
    sys.exit(main())
