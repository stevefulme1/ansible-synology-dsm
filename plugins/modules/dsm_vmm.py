#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_vmm
short_description: Manage Virtual Machine Manager VMs on Synology DSM
description:
  - Create, delete, power on, and power off VMs via VMM on Synology DSM.
  - Requires the Virtual Machine Manager package installed.
version_added: "0.2.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The virtual machine name.
    type: str
    required: true
  state:
    description:
      - Desired state of the virtual machine.
    type: str
    choices: ['present', 'absent', 'started', 'stopped']
    default: present
  vcpus:
    description:
      - Number of virtual CPUs to assign.
    type: int
    default: 1
  memory_mb:
    description:
      - Memory allocation in megabytes.
    type: int
    default: 1024
  disk_size_gb:
    description:
      - Virtual disk size in gigabytes.
    type: int
    default: 20
  network:
    description:
      - Network to attach the VM to.
    type: str
    default: default
  autostart:
    description:
      - Whether the VM starts automatically when DSM boots.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a virtual machine
  stevefulme1.synology_dsm.dsm_vmm:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "ubuntu-server"
    vcpus: 2
    memory_mb: 2048
    disk_size_gb: 40
    autostart: true
    state: present

- name: Power on a VM
  stevefulme1.synology_dsm.dsm_vmm:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "ubuntu-server"
    state: started

- name: Power off a VM
  stevefulme1.synology_dsm.dsm_vmm:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "ubuntu-server"
    state: stopped

- name: Remove a VM
  stevefulme1.synology_dsm.dsm_vmm:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "ubuntu-server"
    state: absent
'''

RETURN = r'''
vm:
  description: Details about the managed virtual machine.
  returned: always
  type: dict
  contains:
    name:
      description: The VM name.
      type: str
      returned: always
    state:
      description: The resulting state.
      type: str
      returned: always
    guest_id:
      description: The VMM guest ID.
      type: str
      returned: when present
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_guest(client, name):
    """Find a VMM guest by name."""
    data = client.request('SYNO.Virtualization.Guest', 'list', version=1,
                          extra_params={'limit': '-1', 'offset': '0'})
    for guest in data.get('guests', []):
        if guest.get('guest_name') == name:
            return guest
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(
            type='str', default='present',
            choices=['present', 'absent', 'started', 'stopped'],
        ),
        vcpus=dict(type='int', default=1),
        memory_mb=dict(type='int', default=1024),
        disk_size_gb=dict(type='int', default=20),
        network=dict(type='str', default='default'),
        autostart=dict(type='bool', default=False),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        existing = find_guest(client, name)

        if state in ('present', 'started'):
            if existing is None:
                changed = True
                if not module.check_mode:
                    create_params = {
                        'additional': json.dumps({
                            'guest_name': name,
                            'vcpu_num': module.params['vcpus'],
                            'vram_size': module.params['memory_mb'],
                            'vdisk_size': module.params['disk_size_gb'] * 1024,
                            'vnics': [{'network': module.params['network']}],
                            'autorun': module.params['autostart'],
                        }),
                    }
                    client.request('SYNO.Virtualization.Guest', 'create', version=1,
                                   extra_params=create_params)
                    if state == 'started':
                        guest = find_guest(client, name)
                        if guest:
                            client.request(
                                'SYNO.Virtualization.Guest', 'poweron', version=1,
                                extra_params={'guest_id': guest['guest_id']},
                            )
            else:
                result['guest_id'] = existing.get('guest_id')
                if state == 'started' and existing.get('status') != 'running':
                    changed = True
                    if not module.check_mode:
                        client.request(
                            'SYNO.Virtualization.Guest', 'poweron', version=1,
                            extra_params={'guest_id': existing['guest_id']},
                        )

        elif state == 'stopped':
            if existing is None:
                module.fail_json(msg='VM {0} not found.'.format(name))
            if existing.get('status') == 'running':
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Virtualization.Guest', 'poweroff', version=1,
                        extra_params={'guest_id': existing['guest_id']},
                    )
            result['guest_id'] = existing.get('guest_id')

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    if existing.get('status') == 'running':
                        client.request(
                            'SYNO.Virtualization.Guest', 'poweroff', version=1,
                            extra_params={'guest_id': existing['guest_id']},
                        )
                    client.request(
                        'SYNO.Virtualization.Guest', 'delete', version=1,
                        extra_params={'guest_id': existing['guest_id']},
                    )

    except DSMError as e:
        module.fail_json(msg='VMM operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, vm=result)


if __name__ == '__main__':
    main()
