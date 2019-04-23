#!/usr/bin/env python3
import sys
import socket
import os


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

    # Load in template
    f = open('docker-compose.yml.tmpl', 'r')
    template = f.read()
    f.close()

    entrypoint_list = [
        "/code/scripts/generate_chn_sysconfig.py", "-o",
        "/config/chnserver.sysconfig", "-s",
        "https://%s" % domain, "-f"
    ]
    compose = open('docker-compose.yml', 'w')
    compose.write(template.format(entrypoint=entrypoint_list))
    compose.close()
    print("Wrote docker-compose.yml")
    #   local_hp_event_logging = input('Local Honeypot Event Logging')
    #   cif_logging_enabled = input('CIF Logging')
    #   cif_url = input('CIF URL')
    #   cif_api_token = input('CIF API Token')
    return 0


if __name__ == "__main__":
    sys.exit(main())
