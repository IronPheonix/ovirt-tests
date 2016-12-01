# Examples

This directory contains many examples to start trying the oVirt modules.

In order to run any example please first modify the _vars.yml_
file with your credentials. It's predefined to Vagrant instance.

```bash
$ cat vars.yml
url: https://ovirt.local/ovirt-engine/api
username: admin@internal
password: 123456
insecure: True
```

Then feel free to modify the example playbook and run it, for example:

```
$ ansible-playbook vm/create.yml
```

Most of the examples contains the example how to create/remove/list the specific oVirt object.
