#!/bin/bash -xe

###########################################################################
################################## NFS ####################################
###########################################################################

set -xe
EXPORTED_DEV="vdc"
MAIN_NFS_DEV="vdb"

setup_device() {
    local device=$1
    local mountpath=$2
    local exportpath=$3
    mkdir -p ${mountpath}
    echo noop > /sys/block/${device}/queue/scheduler
    mkfs.xfs -K -r extsize=1m /dev/${device}
    echo "/dev/${device} ${mountpath} xfs defaults 0 0" >> /etc/fstab
    mount /dev/${device} ${mountpath}
    mkdir -p ${exportpath}
    chmod a+rwx ${exportpath}
    echo "${exportpath} *(rw,sync,no_root_squash,no_all_squash)" >> /etc/exports
    exportfs -a
}

setup_main_nfs() {
    setup_device ${MAIN_NFS_DEV} /exports/nfs_clean /exports/nfs_clean/share1
}


setup_export() {
    setup_device ${EXPORTED_DEV} /exports/nfs_exported /exports/nfs_exported
}


install_deps() {
    yum install -y deltarpm
    yum install -y nfs-utils
}


setup_iso() {
    mkdir -p /exports/iso
    chmod a+rwx /exports/iso
    echo '/exports/iso/ *(rw,sync,no_root_squash,no_all_squash)' \
    >> /etc/exports
    exportfs -a
}


setup_services() {
    systemctl stop firewalld
    systemctl disable firewalld
    systemctl start rpcbind.service
    systemctl start nfs-server.service
    systemctl start nfs-lock.service
    systemctl start nfs-idmap.service
    systemctl enable rpcbind.service
    systemctl enable nfs-server.service
}

nfs() {
    install_deps
    setup_services
    setup_main_nfs
    setup_export
    setup_iso
}


nfs

###########################################################################
################################## iSCSI ##################################
###########################################################################
NUM_LUNS=5

yum install -y deltarpm

yum install -y \
    qemu-guest-agent lvm2 targetcli iscsi-initiator-utils \
    device-mapper-multipath

echo noop > /sys/block/vdb/queue/scheduler
pvcreate /dev/vdd
vgcreate vg1_storage /dev/vdd
extents=$(vgdisplay vg1_storage | grep 'Total PE' | awk '{print $NF;}')
lvcreate -Zn -l$(($extents - 50)) -T vg1_storage/thinpool

targetcli /iscsi create iqn.2014-07.org.ovirt:storage

create_lun () {
    local ID=$1
    lvcreate \
        vg1_storage -V100G --thinpool vg1_storage/thinpool  -n lun${ID}_bdev
    targetcli \
        /backstores/block \
        create name=lun${ID}_bdev dev=/dev/vg1_storage/lun${ID}_bdev
    targetcli \
        /iscsi/iqn.2014-07.org.ovirt:storage/tpg1/luns/ \
        create /backstores/block/lun${ID}_bdev
}


for I in $(seq $NUM_LUNS);
do
    create_lun $(($I - 1));
done;

targetcli /iscsi/iqn.2014-07.org.ovirt:storage/tpg1 \
    set attribute authentication=0 demo_mode_write_protect=0 generate_node_acls=1 cache_dynamic_acls=1
targetcli saveconfig

systemctl enable target
systemctl start target


iscsiadm -m discovery -t sendtargets -p 127.0.0.1
iscsiadm -m node -L all

cat >> /etc/multipath.conf << EOC
### Based on vdsm configuration
defaults {
    polling_interval            5
    no_path_retry               fail
    user_friendly_names         no
    flush_on_last_del           yes
    fast_io_fail_tmo            5
    dev_loss_tmo                30
    max_fds                     4096
}
# Remove devices entries when overrides section is available.
devices {
    device {
        # These settings overrides built-in devices settings. It does not apply
        # to devices without built-in settings (these use the settings in the
        # "defaults" section), or to devices defined in the "devices" section.
        # Note: This is not available yet on Fedora 21. For more info see
        # https://bugzilla.redhat.com/1253799
        all_devs                yes
        no_path_retry           fail
    }
}
EOC

# this is needed so lvm does not use the iscsi volumes
sed -i /etc/lvm/lvm.conf \
    -e 's/^\s*# global_filter.*/global_filter = \["r\|\/dev\/vg1_storage\/\*\|" \]/'


systemctl start multipathd
systemctl enable multipathd
systemctl stop firewalld
systemctl disable firewalld
fstrim -va

###########################################################################
################################## LDAP ###################################
###########################################################################
yum install -y --downloaddir=/dev/shm 389-ds-base

DOMAIN=storage.local
HOSTNAME=$DOMAIN
PASSWORD=12345678
ADDR='192.168.200.13'
cat >> answer_file.inf <<EOC
[General]
FullMachineName= @HOSTNAME@
SuiteSpotUserID= root
SuiteSpotGroup= root
ConfigDirectoryLdapURL= ldap://@HOSTNAME@:389/o=NetscapeRoot
ConfigDirectoryAdminID= admin
ConfigDirectoryAdminPwd= @PASSWORD@
AdminDomain= @DOMAIN@

[slapd]
ServerIdentifier= mycompany
ServerPort= 389
Suffix= dc=mycompany, dc=local
RootDN= cn=Directory Manager
RootDNPwd= @PASSWORD@

[admin]
ServerAdminID= admin
ServerAdminPwd= @PASSWORD@
SysUser= dirsrv
EOC

sed -i 's/@HOSTNAME@/'"$HOSTNAME"'/g' answer_file.inf
sed -i 's/@PASSWORD@/'"$PASSWORD"'/g' answer_file.inf
sed -i 's/@DOMAIN@/'"$DOMAIN"'/g' answer_file.inf

cat >> add_user.ldif <<EOC
dn: uid=user1,ou=People,dc=mycompany,dc=local
uid: user1
givenName: user1
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetorgperson
objectclass: inetuser
sn: user1
cn: user1 user1
userPassword: {SSHA}1e/GY7pCEhoL5yMR8HvjI7+3me6PQtxZ
# Password is 123456
EOC

cat >> add_group.ldif <<EOC
dn: cn=group1,ou=Groups,dc=mycompany,dc=local
objectClass: top
objectClass: groupofuniquenames
uniqueMember: uid=user1,ou=People,dc=mycompany,dc=local
cn: group1
EOC


echo "$ADDR $HOSTNAME" >> /etc/hosts
/usr/sbin/setup-ds.pl --silent --file=answer_file.inf
ldapadd -x -H ldap://localhost -D 'cn=Directory Manager' -w $PASSWORD -f add_user.ldif
ldapadd -x -H ldap://localhost -D 'cn=Directory Manager' -w $PASSWORD -f add_group.ldif
