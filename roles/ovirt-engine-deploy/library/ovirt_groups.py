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
except ImportError:
    pass

from ansible.module_utils.ovirt import *


DOCUMENTATION = '''
---
module: ovirt_groups
short_description: Module to manage groups in oVirt
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage groups in oVirt"
options:
    name:
        description:
            - "Name of the the group to manage."
        required: true
    state:
        description:
            - "Should the group be present/absent."
        choices: ['present', 'absent']
        default: present
    authz_name:
        description:
            - "Authorization provider of the group. In previous versions of oVirt known as domain."
        required: true
        aliases: ['domain']
    namespace:
        description:
            - "Namespace of the authorization provider, where group resides."
        required: false
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add group group1 from authorization provider example.com-authz
ovirt_groups:
    name: group1
    domain: example.com-authz

# Add group group1 from authorization provider example.com-authz
# In case of multi-domain Active Directory setup, you should pass
# also namespace, so it adds correct group:
ovirt_groups:
    name: group1
    namespace: dc=ad2,dc=example,dc=com
    domain: example.com-authz

# Remove group group1 with authorization provider example.com-authz
ovirt_groups:
    state: absent
    name: group1
    domain: example.com-authz
'''


class GroupsModule(BaseModule):

    def build_entity(self):
        return otypes.Group(
            domain=otypes.Domain(
                name=self._module.params['authz_name']
            ),
            name=self._module.params['name'],
            namespace=self._module.params['namespace'],
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(required=True),
        authz_name=dict(required=True, aliases=['domain']),
        namespace=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)
    check_params(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        groups_service = connection.system_service().groups_service()
        groups_module = GroupsModule(
            connection=connection,
            module=module,
            service=groups_service,
        )
        group = search_by_name(
            service=groups_service,
            name=module.params['name'],
            namespace=module.params['namespace'],
        )

        state = module.params['state']
        if state == 'present':
            # Passing `search_params` along with entity is hack here,
            # because it's not possible to find group by it's namespace,
            # and if group is not found by `search_by_name` method, by
            # filtering object attributes, it should be found even,
            # by `create` method, that's why we need to pass everything
            # here and not empty `search_params` otherwise only `name`
            # would be used. In future if oVirt backend will support search
            # by namespace, we can remove it:
            ret = groups_module.create(
                entity=group,
                search_params={
                    'name': module.params['name'],
                    'namespace': module.params['namespace'],
                }
            )
        elif state == 'absent':
            ret = groups_module.remove(
                entity=group,
                search_params={
                    'name': module.params['name'],
                    'namespace': module.params['namespace'],
                }
            )

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e))
    finally:
        connection.close(logout=False)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
