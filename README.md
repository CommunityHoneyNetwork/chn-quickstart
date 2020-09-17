# CHN Quickstart

Tools and helper scripts for use when spinning up a new CHN instance.  Full
documentation [here](https://communityhoneynetwork.readthedocs.io/en/stable/)

## 'Quickstart' or 'Documentation is for Chumps'

Install procedure:

* Install docker & docker-compose
* Ensure python3 & pip3 are available
* `python3 -m pip install -r requirements.txt`
* Clone the [latest release](https://github.com/CommunityHoneyNetwork/chn-quickstart/releases/latest) repository and `cd` into it
* `./guided_docker_compose.py`

Presuming an AWS Ubuntu instance:

* `sudo apt update && sudo apt upgrade -y && sudo apt install -y docker-compose jq python3 python3-pip && sudo python3 -m pip install -r requirements.txt && sudo usermod -aG docker ubuntu && sudo systemctl enable docker && sudo reboot`
* `sudo git clone -b v1.9 https://github.com/CommunityHoneyNetwork/chn-quickstart.git /opt/chnserver && sudo chown -R
 ubuntu:docker /opt/chnserver`
* Run `cd /opt/chnserver && ./guided_docker_compose.py`
* Run `docker-compose up`
