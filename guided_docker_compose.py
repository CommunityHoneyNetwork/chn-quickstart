#!/usr/bin/env python3
import sys
import socket
import os
import argparse
import validators
import secrets
import string
from urllib.parse import urlparse
import re

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


def check_cert_strategy(certificate_strategy, domain):
    """
    If it's an IP addr or localhost, certbot won't issue a cert, so set SELFSIGNED if it matches one of those
    """
    # we assume they know what they're doing if they've elected to bring their own cert
    if certificate_strategy == 'BYO' or certificate_strategy == 'SELFSIGNED':
        return certificate_strategy
    if (validators.ip_address.ipv4(domain) or
            validators.ip_address.ipv6(domain) or
            domain.startswith('localhost')):
        # "Selected cert strategy was CERTBOT but detected IP address or localhost for Base URL\n"
        print(
            make_color(
                "BOLD",
                "Overriding cert strategy to SELFSIGNED since certbot won't issue for IP addresses or localhost")
        )
        print()
        return 'SELFSIGNED'
    else:
        return certificate_strategy


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
            ("Please enter the URL where you'd like your CHN web console available.  Note that the "
             "domain must be resolvable. E.g.: sub.domain.tld or localhost/chn.")))
    domain = None
    cert_strategy = None

    touch('config/sysconfig/chnserver.env')

    while not domain:
        domain = input('Domain: ')
        # if it's a bare fqdn, prepend the proto scheme https so we can use urlparse
        # without a scheme, urlparse puts the full url + path all in netloc attribute of its return object
        # that makes it difficult later to determine if there's a custom path in the url
        if not domain.startswith('http'):
            domain = 'https://' + domain
        url_parsed = urlparse(domain)
        try:
            socket.getaddrinfo(url_parsed.netloc, 443)
        except Exception as e:
            sys.stderr.write(
                make_color("FAIL",
                           "%s is not an active domain name\n" % url_parsed.netloc))
            domain = None

    while not cert_strategy:
        certificate_strategies = {
            'CERTBOT':
                ('Signed certificate by an ACME provider such as LetsEncrypt.  '
                 'Most folks will want to use this.  You must ensure your URL is '
                 'accessible from the ACME hosts for verification here'),
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

    generate_sysconfig(output_file="config/sysconfig/chnserver.env",
                       template_file="templates/chn_server.env.template",
                       server_base_url="https://%s%s" % (
                           url_parsed.netloc, url_parsed.path),
                       password=generate_password(),
                       certificate_strategy=check_cert_strategy(
                           cert_strategy, url_parsed.netloc)
                       )


def configure_mnemosyne():
    retention = None

    while not retention:
        print()
        print(
            make_color(
                "BOLD",
                "How many days of honeypot data should be maintained in the database (default 30 days)?"
            )
        )
        days_str = input("Number of Days: ")
        try:
            days = int(days_str)
            if days < 1:
                print(
                    make_color("FAIL",
                               "%s is not a valid number of days. Please choose a number greater than zero." % days_str)
                )
                continue
            retention = days * 60 * 60 * 24
        except ValueError:
            print(
                make_color("FAIL",
                           "%s is not a valid number." % days_str)
            )
            retention = None

    generate_sysconfig(output_file="config/sysconfig/mnemosyne.env",
                       template_file="templates/mnemosyne.env.template",
                       retention=retention
                       )


def configure_hpfeeds_cif():
    valid_url = None
    valid_token = None
    valid_provider = None

    while not valid_url:
        print()
        cif_server_url = input('Please enter the URL for the remote CIFv3 server: ')
        valid_url = validators.url(cif_server_url)
        if not valid_url:
            print('Invalid URL, please ensure the URL includes the scheme (https://)!')

    while not valid_token:
        print()
        cif_write_token = input('Please enter the *write* API token for the remote CIFv3 server: ')
        if re.match('[0-9a-z]{80}', cif_write_token.strip('\n')):
            valid_token = True
        else:
            print('Input provided did not match expected pattern for a CIF API token!')

    while not valid_provider:
        cif_org = input('Please enter a name you wish to be associated with your organization (partnerX): ')
        if re.match('[a-zA-Z0-9_-]+', cif_org):
            valid_provider = True
        else:
            print('Input provided is not a valid provider ID; valid character set is [a-zA-Z0-9_-]')

    generate_sysconfig(output_file="config/sysconfig/hpfeeds-cif.env",
                       template_file="templates/hpfeeds-cif.env.template",
                       cif_server_url=cif_server_url,
                       cif_token=cif_write_token,
                       cif_org=cif_org,
                       ident=generate_password(8))


def configure_chn_intel_feeds():
    valid_url = None
    valid_read_token = None
    valid_write_token = None
    valid_provider = None

    while not valid_url:
        print()
        cif_server_url = input('Please enter the URL for the remote CIFv3 server: ')
        valid_url = validators.url(cif_server_url)
        if not valid_url:
            print('Invalid URL, please ensure the URL includes the scheme (https://)!')

    while not valid_read_token:
        print()
        cif_read_token = input('Please enter the *read* API token for the remote CIFv3 server: ')
        if re.match('[0-9a-z]{80}', cif_read_token.strip('\n')):
            valid_read_token = True
        else:
            print('Input provided did not match expected pattern for a CIF API token!')

    while not valid_write_token:
        print()
        cif_write_token = input('Please enter the *write* API token for the remote CIFv3 server: ')
        if re.match('[0-9a-z]{80}', cif_write_token.strip('\n')):
            valid_write_token = True
        else:
            print('Input provided did not match expected pattern for a CIF API token!')

    while not valid_provider:
        cif_org = input('Please enter the name associated with your organization safelist (partnerX): ')
        if re.match('[a-zA-Z0-9_-]+', cif_org):
            valid_provider = True
        else:
            print('Input provided is not a valid provider ID; valid character set is [a-zA-Z0-9_-]')

    generate_sysconfig(output_file="config/sysconfig/chn-intel-feeds.env",
                       template_file="templates/chn-intel-feeds.env.template",
                       cif_server_url=cif_server_url,
                       cif_write_token=cif_write_token,
                       cif_read_token=cif_read_token,
                       cif_org=cif_org)


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
                "Raw JSON output from hpfeeds. More verbose that other formats, but also not normalized. Can generate a large amount of data."
        }

        print()
        for fmt, fmt_help in logging_formats.items():
            print("%s: %s" % (fmt, fmt_help))

        log_format = input('Logging Format: ')
        if log_format not in logging_formats.keys():
            print()
            sys.stderr.write(
                make_color(
                    "FAIL", "You must use one of %s\n" %
                            logging_formats.keys()))
            log_format = None

    generate_sysconfig(output_file="config/sysconfig/hpfeeds-logger.env",
                       template_file="templates/hpfeeds-logger.env.template",
                       log_format=log_format,
                       ident=generate_password(8))


def main():

    chn_sysconfig_exists = os.path.exists(
        "config/sysconfig/chnserver.env")

    reconfig = False
    if chn_sysconfig_exists:
        answer = input(make_color("BOLD",
                                  "Previous chn-server.env file detected. Do you wish to reconfigure? [y/N]: "))
        reconfig = answer.lower() == ("y" or "yes")

    if reconfig or not chn_sysconfig_exists:
        configure_chn()
        configure_mnemosyne()

    write_docker_compose(
        "templates/docker-compose.yml.template", "docker-compose.yml", 'w')

    # Check if user wants to enable hpfeeds-cif
    cif_sysconfig_exists = os.path.exists(
        "config/sysconfig/hpfeeds-cif.env")

    reconfig = False
    enable_cif = False
    if cif_sysconfig_exists:
        answer = input(make_color("BOLD",
                                  "Previous hpfeeds-cif.env file detected. Do you wish to reconfigure? [y/N]: "))
        reconfig = answer.lower() == ("y" or "yes")
    else:
        answer = input(make_color("BOLD",
                                  "Do you wish to enable logging to a remote CIFv3 server? [y/N]: "))
        enable_cif = answer.lower() == ("y" or "yes")

    if enable_cif or reconfig:
        configure_hpfeeds_cif()

    if enable_cif or reconfig or cif_sysconfig_exists:
        write_docker_compose(
            "templates/docker-compose-cif.yml.template", "docker-compose.yml", 'a')

    # Check if user wants to enable hpfeeds-logger
    logger_sysconfig_exists = os.path.exists(
        "config/sysconfig/hpfeeds-logger.env")

    reconfig = False
    enable_logger = False
    if logger_sysconfig_exists:
        answer = input(make_color("BOLD",
                                  "Previous hpfeeds-logger.env file detected. Do you wish to reconfigure? [y/N]: "))
        reconfig = answer.lower() == ("y" or "yes")
    else:
        answer = input(make_color("BOLD",
                                  "Do you wish to enable logging to a local file? [y/N]: "))
        enable_logger = answer.lower() == ("y" or "yes")

    if enable_logger or reconfig:
        configure_hpfeeds_logger()

    if enable_logger or reconfig or logger_sysconfig_exists:
        write_docker_compose(
            "templates/docker-compose-log.yml.template", "docker-compose.yml", 'a')

    # Check if user wants to enable hpfeeds-logger
    feeds_exists = os.path.exists(
        "config/sysconfig/chn-intel-feeds.env")

    reconfig = False
    enable_feeds = False
    if feeds_exists:
        answer = input(make_color("BOLD",
                                  "Previous chn-intel-feeds.env file detected. Do you wish to reconfigure? [y/N]: "))
        reconfig = answer.lower() == ("y" or "yes")
    else:
        answer = input(make_color("BOLD",
                                  "Do you wish to enable intelligence feeds from a remote CIF instance? [y/N]: "))
        enable_feeds = answer.lower() == ("y" or "yes")

    if enable_feeds or reconfig:
        configure_chn_intel_feeds()

    if enable_feeds or reconfig or feeds_exists:
        write_docker_compose(
            "templates/docker-compose-chn-intel-feeds.yml.template", "docker-compose.yml", 'a')


if __name__ == "__main__":
    main()
