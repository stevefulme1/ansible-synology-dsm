#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_usb_copy
short_description: Configure USB Copy tasks on Synology DSM
description:
  - Create, update, or delete USB Copy tasks on a Synology DSM device.
  - Supports configuring copy direction, source and destination paths.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the USB Copy task.
    type: str
    required: true
  source_path:
    description:
      - Source path for the copy operation.
    type: str
  dest_path:
    description:
      - Destination path for the copy operation.
    type: str
  direction:
    description:
      - Copy direction between USB and NAS.
    type: str
    choices: ['usb_to_nas', 'nas_to_usb']
    default: usb_to_nas
  enabled:
    description:
      - Whether the USB Copy task is enabled.
    type: bool
    default: true
  state:
    description:
      - Whether the USB Copy task should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create USB Copy task
  stevefulme1.synology_dsm.dsm_usb_copy:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "backup_photos"
    source_path: "/volumeUSB1/usbshare"
    dest_path: "/volume1/photos"
    direction: usb_to_nas
    state: present

- name: Remove USB Copy task
  stevefulme1.synology_dsm.dsm_usb_copy:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "backup_photos"
    state: absent
'''

RETURN = r'''
usb_copy:
  description: USB Copy task configuration.
  returned: always
  type: dict
  contains:
    name:
      description: Task name.
      type: str
      returned: always
    state:
      description: Resulting state.
      type: str
      returned: always
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_task(client, name):
    """Find a USB Copy task by name."""
    data = client.request('SYNO.Core.ExternalDevice.UsbCopy', 'list', version=1)
    for task in data.get('tasks', []):
        if task.get('name') == name:
            return task
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        source_path=dict(type='str'),
        dest_path=dict(type='str'),
        direction=dict(type='str', default='usb_to_nas', choices=['usb_to_nas', 'nas_to_usb']),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['source_path', 'dest_path']),
        ],
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        existing = find_task(client, name)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    params = {
                        'name': name,
                        'source_path': module.params['source_path'],
                        'dest_path': module.params['dest_path'],
                        'direction': module.params['direction'],
                        'enabled': str(module.params['enabled']).lower(),
                    }
                    client.request('SYNO.Core.ExternalDevice.UsbCopy', 'create',
                                   version=1, extra_params=params)
            else:
                needs_update = (
                    existing.get('source_path') != module.params['source_path']
                    or existing.get('dest_path') != module.params['dest_path']
                    or existing.get('direction') != module.params['direction']
                    or existing.get('enabled') != module.params['enabled']
                )
                if needs_update:
                    changed = True
                    if not module.check_mode:
                        params = {
                            'name': name,
                            'source_path': module.params['source_path'],
                            'dest_path': module.params['dest_path'],
                            'direction': module.params['direction'],
                            'enabled': str(module.params['enabled']).lower(),
                        }
                        client.request('SYNO.Core.ExternalDevice.UsbCopy', 'set',
                                       version=1, extra_params=params)

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Core.ExternalDevice.UsbCopy', 'delete',
                                   version=1, extra_params={'name': json.dumps([name])})

    except DSMError as e:
        module.fail_json(msg='USB Copy operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, usb_copy=result)


if __name__ == '__main__':
    main()
