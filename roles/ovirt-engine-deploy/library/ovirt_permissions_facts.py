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
except ImportError:
    pass

from ansible.module_utils.ovirt import *

DOCUMENTATION = '''
---
module: ovirt_permissions_facts
short_description: Retrieve facts about one or more oVirt permissions
version_added: "2.3"
description:
    - "Retrieve facts about one or more oVirt permissions."
notes:
    - "This module creates a new top-level C(ovirt_permissions) fact, which
       contains a list of permissions."
requirements:
    - python >= 2.7
    - ovirt-engine-sdk-python >= 4.0.0
options:
    user_name:
        description:
            - "Username of the the user to manage. In most LDAPs it's I(uid) of the user, but in Active Directory you must specify I(UPN) of the user."
    group_name:
        description:
            - "Name of the the group to manage."
    authz_name:
        description:
            - "Authorization provider of the user/group. In previous versions of oVirt known as domain."
        required: true
        aliases: ['domain']
    namespace:
        description:
            - "Namespace of the authorization provider, where user/group resides."
        required: false
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about all permissions of user john:
- ovirt_permissions_facts:
    user_name: john
    authz_name: example.com-authz
- debug:
    var: ovirt_permissions
'''

RETURN = '''
ovirt_permissions:
    description: "Dictionary describing the permissions. Permission attribues are mapped to dictionary keys,
                  all permissions attributes can be found at following url: https://ovirt.example.com/ovirt-engine/api/model#types/permission."
    returned: On success.
    type: dictionary
'''


def _permissions_service(connection, module):
    if module.params['user_name']:
        service = connection.system_service().users_service()
        entity = search_by_name(service, module.params['user_name'])
    else:
        service = connection.system_service().groups_service()
        entity = search_by_name(service, module.params['group_name'])

    if entity is None:
        raise Exception("User/Group wasn't found.")

    return service.service(entity.id).permissions_service()


def main():
    argument_spec = ovirt_full_argument_spec(
        authz_name=dict(required=True, aliases=['domain']),
        user_name=dict(rdefault=None),
        group_name=dict(default=None),
        namespace=dict(default=None),
    )
    module = AnsibleModule(argument_spec)
    check_sdk(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        permissions_service = _permissions_service(connection, module)
        permissions = []
        for p in permissions_service.list():
            newperm = dict()
            for key, value in p.__dict__.items():
                if value and isinstance(value, sdk.Struct):
                    newperm[key[1:]] = get_link_name(connection, value)
            permissions.append(newperm)
        
        module.exit_json(
            changed=False,
            ansible_facts=dict(ovirt_permissions=permissions),
        )
    except Exception as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()