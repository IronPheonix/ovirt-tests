#!/bin/bash
#sudo echo "nameserver 8.8.8.8" > /etc/resolv.conf

REALEASE_41=http://resources.ovirt.org/pub/yum-repo/ovirt-release41-pre.rpm
REALEASE_40=http://resources.ovirt.org/pub/yum-repo/ovirt-release40-pre.rpm
sudo yum localinstall -y $REALEASE_41

sudo yum install -y epel-release
sudo yum install -y haveged
sudo yum install -y ansible
sudo yum install -y vdsm-python
sudo yum install -y ovirt-engine
sudo yum install -y ovirt-engine-extension-aaa-ldap*

cat > /root/iso-uploader.conf << EOF
[ISOUploader]
user=admin@internal
passwd=123456
engine=ovirt.local:443
EOF
