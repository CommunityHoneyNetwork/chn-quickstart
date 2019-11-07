# CHN Quickstart

Tools and helper scripts for use when spinning up a new CHN instance.  Full
documentation [here](https://communityhoneynetwork.readthedocs.io/en/stable/)

## 'Quickstart' or 'Documentation is for Chumps'

Presuming an AWS Ubuntu instance:

* `sudo apt update && sudo apt upgrade -y && sudo apt install -y docker-compose jq python3 python3-pip && sudo pip3 install validators && sudo usermod -aG docker ubuntu && sudo systemctl enable docker && sudo reboot`
* `sudo git clone https://github.com/CommunityHoneyNetwork/chn-quickstart.git /opt/chnserver && sudo chown -R ubuntu:docker /opt/chnserver`
* Run `cd /opt/chnserver && ./guided_docker_compose.py`
* Run `docker-compose up`
