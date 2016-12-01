#!/bin/bash
sudo echo "nameserver 8.8.8.8" > /etc/resolv.conf

sudo yum update -y

REALEASE_41=http://resources.ovirt.org/pub/yum-repo/ovirt-release41-pre.rpm
REALEASE_40=http://resources.ovirt.org/pub/yum-repo/ovirt-release40-pre.rpm
sudo yum localinstall -y $REALEASE_41

sudo yum install -y vdsm
sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd
