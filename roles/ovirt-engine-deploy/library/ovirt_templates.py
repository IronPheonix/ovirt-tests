#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
module: ovirt_templates
short_description: Module to create/delete templates in oVirt/RHV
version_added: "2.2"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to create/delete templates in oVirt/RHV"
options:
    name:
        description:
            - "Name of the the template to manage."
        required: true
    state:
        description:
            - "Should the template be present/absent/exported/imported"
        choices: ['present', 'absent', 'exported', 'imported']
        default: present
    vm_name:
        description:
            - "Name of the VM, which will be used to create template."
    description:
        description:
            - "Description of the template."
    cpu_profile:
        description:
            - "CPU profile to be set to template."
    cluster:
        description:
            - "Name of the cluster, where template should be created/imported."
    exclusive:
        description:
            - "When C(state) is I(exported) this parameter indicates if the existing templates with the
               same name should be overwritten."
    export_domain:
        description:
            - "When C(state) is I(exported) or I(imported) this parameter specifies the name of the
               export storage domain."
    image_provider:
        description:
            - "When C(state) is I(imported) this parameter specifies the name of the image provider to be used."
    image_disk:
        description:
            - "When C(state) is I(imported) and C(image_provider) is used this parameter specifies the name of disk
               to be imported as template."
    storage_domain:
        description:
            - "When C(state) is I(imported) this parameter specifies the name of the destination data storage domain."
    clone_permissions:
        description:
            - "If I(True) then the permissions of the VM (only the direct ones, not the inherited ones)
            will be copied to the created template."
            - "This parameter is used only when C(state) I(present)."
        default: False
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create template from vm
- ovirt_templates:
    cluster: Default
    name: mytemplate
    vm_name: rhel7
    cpu_profile: Default
    description: Test

# Import template
- ovirt_templates:
  state: imported
  name: mytemplate
  export_domain: myexport
  storage_domain: mystorage
  cluster: mycluster

# Remove template
- ovirt_templates:
    state: absent
    name: mytemplate
'''


class TemplatesModule(BaseModule):

    def build_entity(self):
        return otypes.Template(
            name=self._module.params['name'],
            cluster=otypes.Cluster(
                name=self._module.params['cluster']
            ) if self._module.params['cluster'] else None,
            vm=otypes.Vm(
                name=self._module.params['vm_name']
            ) if self._module.params['vm_name'] else None,
            description=self._module.params['description'],
            cpu_profile=otypes.CpuProfile(
                id=search_by_name(
                    self._connection.system_service().cpu_profiles_service(),
                    self._module.params['cpu_profile'],
                ).id
            ) if self._module.params['cpu_profile'] else None,
        )

    def update_check(self, entity):
        return (
            equal(self._module.params.get('cluster'), get_link_name(self._connection, entity.cluster)) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self._module.params.get('cpu_profile'), get_link_name(self._connection, entity.cpu_profile))
        )

    def _get_export_domain_service(self):
        provider_name = self._module.params['export_domain'] or self._module.params['image_provider']
        if self._module.params['image_provider']:
            # Can be removed when python sdk v 4.0.3
            export_sds_service = self._connection.system_service().openstack_image_providers_service()
        else:
            export_sds_service = self._connection.system_service().storage_domains_service()

        export_sd = search_by_name(export_sds_service, provider_name)
        if export_sd is None:
            raise ValueError(
                "Export storage domain/Image Provider '%s' wasn't found." % provider_name
            )

        # Locate export storage domain templates service or glance provider service:
        return export_sds_service.service(export_sd.id)

    def post_export_action(self, entity):
        self._service = self._get_export_domain_service().templates_service()

    def post_import_action(self, entity):
        self._service = self._connection.system_service().templates_service()


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent', 'exported', 'imported'],
            default='present',
        ),
        name=dict(default=None),
        vm_name=dict(default=None),
        description=dict(default=None),
        cluster=dict(default=None),
        cpu_profile=dict(default=None),
        disks=dict(default=[], type='list'),
        clone_permissions=dict(type='bool'),
        export_domain=dict(default=None),
        storage_domain=dict(default=None),
        exclusive=dict(type='bool'),
        image_provider=dict(default=None),
        image_disk=dict(default=None),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)
    check_params(module)

    try:
        # Create connection to engine and clusters service:
        connection = create_connection(module.params.pop('auth'))
        templates_service = connection.system_service().templates_service()
        templates_module = TemplatesModule(
            connection=connection,
            module=module,
            service=templates_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = templates_module.create(
                result_state=otypes.TemplateStatus.OK,
                clone_permissions=module.params['clone_permissions'],
            )
        elif state == 'absent':
            ret = templates_module.remove()
        elif state == 'exported':
            template = templates_module.search_entity()
            export_service = templates_module._get_export_domain_service()
            export_template = search_by_attributes(export_service.templates_service(), id=template.id)

            ret = templates_module.action(
                entity=template,
                action='export',
                action_condition=lambda t: export_template is None,
                wait_condition=lambda t: t is not None,
                post_action=templates_module.post_export_action,
                storage_domain=otypes.StorageDomain(id=export_service.get().id),
                #exclusive=module.params['exclusive'],
            )
        elif state == 'imported':
            template = templates_module.search_entity()
            export_service = templates_module._get_export_domain_service()

            kwargs = {}
            if module.params['image_provider']:
                # FIXME: TEMP WorkAround
                sd = connection.system_service().storage_domains_service().list(search='name=%s' % module.params['image_provider'])[0]
                connection.system_service().storage_domains_service().service(sd.id).images_service().list()
                ########################

                kwargs.update(
                    disk=otypes.Disk(
                        name=module.params['image_disk']
                    ),
                    template=otypes.Template(
                        name=module.params['name'],
                    ),
                    import_as_template=True,
                )
                templates_module._service = export_service.images_service()
                entity = search_by_name(export_service.images_service(), module.params['image_disk'])
            else:
                entity = templates_module.search_entity()
                templates_module._service = export_service.templates_service()

            ret = templates_module.action(
                entity=entity,
                action='import_',
                action_condition=lambda t: template is None,
                storage_domain=otypes.StorageDomain(
                    name=module.params['storage_domain']
                ) if module.params['storage_domain'] else None,
                cluster=otypes.Cluster(
                    name=module.params['cluster']
                ) if module.params['cluster'] else None,
                **kwargs
            )
            for i in range(0, 20):
                template = search_by_name(templates_service, module.params['name'])
                if template:
                    break
                import time
                time.sleep(5)

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e))
    finally:
        # Close the connection to the server, don't revoke token:
        connection.close(logout=False)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
