FROM ubuntu:18.04

LABEL maintainer="Team Stingar <team-stingar@duke.edu>"
LABEL name="chn-config"
LABEL version="1.9.1"
LABEL release="1"
# hadolint ignore=DL3008,DL3005
ENV DEBIAN_FRONTEND "noninteractive"

VOLUME /config

# hadolint ignore=DL3008,DL3005
RUN apt-get update \
    && apt-get install --no-install-recommends -y ansible python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /code
COPY . /code

RUN python3 -m pip install --upgrade pip setuptools wheel \
  && python3 -m pip install -r /code/requirements.txt

ENTRYPOINT [ "/code/scripts/generate_chn_sysconfig.py", "-o", "/config/chnserver.sysconfig", "-s", "https://myhome.com" ]
