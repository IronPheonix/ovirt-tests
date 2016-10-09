#!/bin/bash

sudo yum update -y
sudo yum install -y epel-release
sudo yum localinstall -y http://resources.ovirt.org/pub/yum-repo/ovirt-release40.rpm
sudo yum install -y vdsm
sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd
