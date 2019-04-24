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


def write_docker_compose(template_file, output_file, mode='w'):
    f = open(template_file, 'r')
    template = f.read()
    f.close()

    compose = open(output_file, mode)
    compose.write(template)
    compose.write("\n")
    compose.close()


def configure_chn():
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


def configure_hpfeeds_cif():
    cif_server_url = input('Please enter the URL for the remote CIFv3 server: ')
    cif_token = input('Please enter the API token for the remote CIFv3 server: ')
    cif_org = input('Please enter a name you wish to be associated with your organization: ')

    generate_sysconfig(output_file="config/sysconfig/hpfeeds-cif.sysconfig",
                       template_file="templates/hpfeeds-cif.sysconfig.template",
                       cif_server_url=cif_server_url,
                       cif_token=cif_token,
                       cif_org=cif_org,
                       ident=generate_password(8))


def configure_hpfeeds_logger():
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


def main():

    chn_sysconfig_exists = os.path.exists("config/sysconfig/chnserver.sysconfig")

    reconfig = False
    if chn_sysconfig_exists:
        answer = input(make_color("BOLD",
                                  "Previous chn-server.sysconfig file detected. Do you wish to reconfigure? [Y/n]: "))
        reconfig = answer.lower() == ("y" or "yes")

    if reconfig or not chn_sysconfig_exists:
        configure_chn()

    write_docker_compose("templates/docker-compose.yml.template", "docker-compose.yml", 'w')

    # Check if user wants to enable hpfeeds-cif
    cif_sysconfig_exists = os.path.exists("config/sysconfig/hpfeeds-cif.sysconfig")

    reconfig = False
    enable_cif = False
    if cif_sysconfig_exists:
        answer = input(make_color("BOLD",
                                  "Previous hpfeeds-cif.sysconfig file detected. Do you wish to reconfigure? [Y/n]: "))
        reconfig = answer.lower() == ("y" or "yes")
    else:
        answer = input(make_color("BOLD",
                                  "Do you wish to enable logging to a remote CIFv3 server? [Y/n]: "))
        enable_cif = answer.lower() == ("y" or "yes")

    if enable_cif or reconfig:
        configure_hpfeeds_cif()

    if enable_cif or reconfig or cif_sysconfig_exists:
        write_docker_compose("templates/docker-compose-cif.yml.template", "docker-compose.yml", 'a')

    # Check if user wants to enable hpfeeds-logger
    logger_sysconfig_exists = os.path.exists("config/sysconfig/hpfeeds-logger.sysconfig")

    reconfig = False
    enable_logger = False
    if logger_sysconfig_exists:
        answer = input(make_color("BOLD",
                                  "Previous hpfeeds-logger.sysconfig file detected. Do you wish to reconfigure? [Y/n]: "))
        reconfig = answer.lower() == ("y" or "yes")
    else:
        answer = input(make_color("BOLD",
                                  "Do you wish to enable logging to a local file? [Y/n]: "))
        enable_logger = answer.lower() == ("y" or "yes")

    if enable_logger or reconfig:
        configure_hpfeeds_logger()

    if enable_logger or reconfig or logger_sysconfig_exists:
        write_docker_compose("templates/docker-compose-log.yml.template", "docker-compose.yml", 'a')


if __name__ == "__main__":
    main()
