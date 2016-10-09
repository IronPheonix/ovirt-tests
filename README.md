## oVirt modules Ansible tests
# Prerequisites
* Vagrant
* Ansible 2.2
* Libvirt

```
yum install -y vagrant ansible libvirt
```

Add _ovirt.local_ to /etc/hosts, as in oVirt 4.0 you should access only with fqdn to engine.
```
echo '192.168.200.4 ovirt.local ovirt.local' >> /etc/hosts
```

If you have ansible lower then version 2.2 you need to do following:
```
sudo wget https://raw.githubusercontent.com/ansible/ansible/devel/lib/ansible/module_utils/ovirt.py -O /usr/lib/python2.7/site-packages/ansible/module_utils/ovirt.py
```

# How to

First you need to clone the repo:
```
git clone git@github.com:machacekondra/ovirt-tests.git
cd ovirt-tests
```

To setup everything (engine, two hosts, storage, 389ds) run following (note it's deployed parallel):
```
vagrant up
```

To re-run only ansible provision of engine content run:
```
vagrant provision engine --provision-with ansible
```

If you want to setup just storage for example you should run:
```
vagrant up storage
```

To deploy just aaa:
```
ansible-playbook --limit engine engine.yml -t aaa
```

To destroy only the oVirt engine objects not content of vms:
```
ansible-playbook --limit engine engine.yml -t destroy -e destroy=true
```

To destroy env:
```
vagrant destroy
```

To destroy just storage:
```
vagrant destroy storage
```
