FROM ubuntu:18.04

LABEL maintainer Drew Stinnett <drew.stinnett@duke.edu>
LABEL name "chn-config"
LABEL version "0.1"
LABEL release "1"

VOLUME /config

RUN apt-get update \
      && apt-get install -y ansible

RUN mkdir /code
ADD . /code
RUN apt-get install -y python3-pip

RUN pip3 install -r /code/requirements.txt

ENTRYPOINT [ "/code/scripts/generate_chn_sysconfig.py", "-o", "/config/chnserver.sysconfig", "-s", "https://myhome.com" ]
