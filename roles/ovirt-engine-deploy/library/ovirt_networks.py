#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

try:
    import ovirtsdk4 as sdk
    import ovirtsdk4.types as otypes
    HAS_SDK = True
except ImportError:
    HAS_SDK = False

from ansible.module_utils.ovirt import *


DOCUMENTATION = '''
---
module: ovirt_networks
short_description: Module to manage logical networks in oVirt
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage logical networks in oVirt"
options:
    name:
        description:
            - "Name of the the network to manage."
        required: true
    state:
        description:
            - "Should the network be present or absent"
        choices: ['present', 'absent']
        default: present
    datacenter:
        description:
            - "Datacenter name where network reside."
    description:
        description:
            - "Description of the network."
    comment:
        description:
            - "Comment of the network."
    vlan_tag:
        description:
            - "Specify VLAN tag."
    vm_network:
        description:
            - "If I(True) network will be marked as network for VM."
    mtu:
        description:
            - "Maximum transmission unit (MTU) of the network."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create network
- ovirt_networks:
    auth: "{{ ovirt_auth }}"
    datacenter: mydatacenter
    name: mynetwork
    vlan_tag: 1
    vm_network: true

# Remove network
- ovirt_networks:
    state: absent
    name: mynetwork
'''

RETURN = '''
id:
    description: "ID of the managed network"
    returned: "On success if network is found."
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
network:
    description: "Dictionary of all the network attributes. Network attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/network."
    returned: "On success if network is found."
'''


class NetworksModule(BaseModule):

    def build_entity(self):
        return otypes.Network(
            name=self._module.params['name'],
            comment=self._module.params['comment'],
            description=self._module.params['description'],
            data_center=otypes.DataCenter(
                name=self._module.params['datacenter'],
            ) if self._module.params['datacenter'] else None,
            vlan=otypes.Vlan(
                self._module.params['vlan_tag'],
            ) if self._module.params['vlan_tag'] else None,
            usages=[
                otypes.NetworkUsage.VM if self._module.params['vm_network'] else None
            ] if self._module.params['vm_network'] is not None else None,
            mtu=self._module.params['mtu'],
        )

    def update_check(self, entity):
        return (
            equal(self._module.params.get('comment'), entity.comment) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self._module.params.get('vlan_tag'), getattr(entity.vlan, 'id', None)) and
            equal(self._module.params.get('vm_network'), True if entity.usages else False) and
            equal(self._module.params.get('mtu'), entity.mtu)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        datacenter=dict(default=None, required=True),
        name=dict(default=None, required=True),
        description=dict(default=None),
        comment=dict(default=None),
        vlan_tag=dict(default=None, type='int'),
        vm_network=dict(default=None, type='bool'),
        mtu=dict(default=None, type='int'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)
    check_params(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        networks_service = connection.system_service().networks_service()
        networks_module = NetworksModule(
            connection=connection,
            module=module,
            service=networks_service,
        )
        state = module.params['state']
        network = networks_module.search_entity(
            search_params={
                'name': module.params['name'],
                'datacenter': module.params['datacenter'],
            },
        )
        if state == 'present':
            ret = networks_module.create(entity=network)
        elif state == 'absent':
            ret = networks_module.remove(entity=network)

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e))
    finally:
        connection.close(logout=False)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
