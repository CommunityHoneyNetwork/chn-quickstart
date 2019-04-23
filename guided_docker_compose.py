#!/usr/bin/env python3
import sys
import socket
import os
import argparse
import validators
import secrets
import string


def make_color(color, msg):
    bcolors = {
        'HEADER': '\033[95m',
        'OKBLUE': '\033[94m',
        'OKGREEN': '\033[92m',
        'WARNING': '\033[93m',
        'FAIL': '\033[91m',
        'ENDC': '\033[0m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
    }
    return bcolors[color] + "%s" % msg + bcolors['ENDC']


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


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


def generate_sysconfig(output_file, template_file, force_overwrite=True, **kwargs):
    with open(template_file) as sysconfig_template_file:
        template = sysconfig_template_file.read().format(**kwargs)

    if not os.path.exists(output_file) or force_overwrite:
        f = open(output_file, 'w')
        f.write(template)
        f.close()
        print("Wrote file to %s" % output_file)
    else:
        sys.stderr.write("Not writing file, add -f to override\n")


def main():

    print(
        make_color(
            "BOLD",
            ("Please enter the domain for your CHN Instance.  Note that this "
             "must be a resolvable domain.")))
    domain = None
    cert_strategy = None

    touch('config/sysconfig/chnserver.sysconfig')

    while not domain:
        domain = input('Domain: ')

        try:
            socket.gethostbyname(domain)
        except Exception as e:
            sys.stderr.write(
                make_color("FAIL",
                           "%s is not an active domain name\n" % domain))
            domain = None

    while not cert_strategy:
        certificate_strategies = {
            'CERTBOT':
            ('Signed certificate by an ACME provider such as LetsEncrypt.  '
             'Most folks will want to use this.  You must ensure your URL is '
             'accessable from the ACME hosts for verification here'),
            'BYO':
            ("Bring Your Own.  Use this if you already have a signed cert"
             ", or if you want a real certificate without CertBot"),
            'SELFSIGNED':
            "Generate a simple self-signed certificate"
        }
        print(
            make_color(
                "BOLD",
                "Please enter a Certificate Strategy.  This should be one of:")
        )
        print()
        for strat, strat_help in certificate_strategies.items():
            print("%s: %s" % (strat, strat_help))

        cert_strategy = input('Certificate Strategy: ')
        if cert_strategy not in certificate_strategies.keys():
            print()
            sys.stderr.write(
                make_color(
                    "FAIL", "You must use one of %s\n" %
                    certificate_strategies.keys()))
            cert_strategy = None

    generate_sysconfig(output_file="config/sysconfig/chnserver.sysconfig",
                       template_file="templates/chn_server.sysconfig.template",
                       server_base_url="https://%s" % domain,
                       password=generate_password(),
                       certificate_strategy=cert_strategy)

    # Load in template
    f = open('templates/docker-compose.yml.template', 'r')
    template = f.read()
    f.close()

    compose = open('docker-compose.yml', 'w')
    compose.write(template)
    compose.close()
    print("Wrote docker-compose.yml")

    print()

    cif_logging_enabled = input(make_color("BOLD",
                                           "Do you wish to enable logging to a remote CIFv3 server? [Y/n]: "))
    if cif_logging_enabled.lower() == ("y" or "yes"):
        cif_server_url = input('Please enter the URL for the remote CIFv3 server: ')
        cif_token = input('Please enter the API token for the remote CIFv3 server: ')
        cif_org = input('Please enter a name you wish to be associated with your organization: ')

        generate_sysconfig(output_file="config/sysconfig/hpfeeds-cif.sysconfig",
                           template_file="templates/hpfeeds-cif.sysconfig.template",
                           cif_server_url=cif_server_url,
                           cif_token=cif_token,
                           cif_org=cif_org,
                           ident=generate_password(8))
        f = open('templates/docker-compose-cif.yml.template', 'r')
        template = f.read()
        f.close()

        compose = open('docker-compose.yml', 'a')
        compose.write(template)
        compose.write("\n")
        compose.close()
        print("Updated docker-compose.yml")

    print()

    local_logging_enabled = input(make_color("BOLD",
                                             "Do you wish to enable logging to a local file? [Y/n]: "))
    if local_logging_enabled.lower() == ("y" or "yes"):
        log_format = None
        while not log_format:
            logging_formats = {
                'splunk':
                'Comma delimited key/value logging format for use with Splunk',
                'json':
                "JSON formatted log format",
                'arcsight':
                "Log format for use with ArcSight SIEM appliances",
                'json_raw':
                ("Raw JSON output from hpfeeds. More verbose that other formats,",
                 "but also not normalized. Can generate a large amount of data.")
            }
            print(
                make_color(
                    "BOLD",
                    "Please enter a Certificate Strategy.  This should be one of:")
            )

            print()
            for fmt, fmt_help in logging_formats.items():
                print("%s: %s" % (fmt, fmt_help))

            log_format = input('Logging Format: ')
            if log_format not in logging_formats.keys():
                print()
                sys.stderr.write(
                    make_color(
                        "FAIL", "You must use one of %s\n" %
                                log_format.keys()))
                log_format = None

        generate_sysconfig(output_file="config/sysconfig/hpfeeds-logger.sysconfig",
                           template_file="templates/hpfeeds-logger.sysconfig.template",
                           log_format=log_format,
                           ident=generate_password(8))
        f = open('templates/docker-compose-log.yml.template', 'r')
        template = f.read()
        f.close()

        compose = open('docker-compose.yml', 'a')
        compose.write(template)
        compose.write("\n")
        compose.close()
        print("Updated docker-compose.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
