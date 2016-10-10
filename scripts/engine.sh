#!/bin/bash

sudo yum install -y http://resources.ovirt.org/pub/yum-repo/ovirt-release40.rpm
sudo yum install -y epel-release
sudo yum install -y haveged
sudo yum install -y ansible
sudo yum install -y vdsm-python
sudo yum install -y ovirt-engine
sudo yum install -y ovirt-engine-extension-aaa-ldap*
# We need Python SDK version 4.0.2
sudo yum update -y http://jenkins.ovirt.org/job/ovirt-engine-sdk_4.0_build-artifacts-el7-x86_64/55/artifact/exported-artifacts/python-ovirt-engine-sdk4-4.0.2-1.el7.centos.x86_64.rpm

cat > /root/iso-uploader.conf << EOF
[ISOUploader]
user=admin@internal
passwd=123456
engine=ovirt.local:443
EOF
