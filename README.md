# oVirt modules Ansible tests

This repo contains auto tests for oVirt Ansible modules using Vagrant.

## Prerequisites
* Fedora 24+/Centos 7.2+
* Vagrant
* Ansible 2.2
* Enabled [nested virtualization](https://fedoraproject.org/wiki/How_to_enable_nested_virtualization_in_KVM)
* ~20GiB of space/8GiB RAM

```
$ yum install -y vagrant ansible @virtualization
$ systemctl start libvirtd
```

Enable [nested virtualization](https://fedoraproject.org/wiki/How_to_enable_nested_virtualization_in_KVM).

Add _ovirt.local_ to /etc/hosts, as in oVirt 4.0 you should access only with fqdn to engine.
```
echo '192.168.200.10 ovirt.local ovirt.local' >> /etc/hosts
```

## Environment description
Vagrant will create four virtual machines:

| Name          | Hostname      | IP             | Description              |
|:------------- |:------------- |:-------------- |:------------------------ |
| engine        | engine.local  | 192.168.200.10 | Contains oVirt engine    |
| host1         | host1.local   | 192.168.200.11 | Contains centos 7.2 host |
| host2         | host2.local   | 192.168.200.12 | Contains centos 7.2 host |
| storage       | storage.local | 192.168.200.13 | Contains NFS/iSCSI/389ds |

For more information please take a look at Vagrantfile and scripts directory,
which contains deploy bash scripts for those machines.

## Run

Clone the repo:
```
git clone git@github.com:machacekondra/ovirt-tests.git
cd ovirt-tests
```

To deploy environment (note it's deployed parallel):
```
vagrant up
```

Wait like ~20minutes. Your engine is now running at https://ovirt.local/ovirt-engine/

## Re-running modified deploy playbooks

To re-run only ansible provision of engine content run:
```
vagrant provision engine --provision-with ansible
```

To re-deploy the storage, you man destroy it and create it again:
```
vagrant destroy storage
vagrant up storage
```

To destroy whole env:
```
vagrant destroy
```

To re-deploy just AAA:
```
ansible-playbook --limit engine engine.yml -t aaa
```

To destroy only the oVirt engine objects not content of vms:
```
ansible-playbook --limit engine destroy.yml
```

Note that this project is using ansible.cfg configuration file,
so I presume you don't have setup ANSIBLE_INVENOTRY environment variable.

## Negative tests
Negative tests are in _negative_ directory.
Negative tests can be run by issuing following command:

```
ansible-playbook negative.yml
```

If you do change only to *ovirt_users* module for example,
you can run just users negative tests by running:

```
ansible-playbook negative.yml -t users
```

## Examples

See [examples](examples/README.md).
