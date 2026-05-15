#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_storage_pool
short_description: Manage storage pools on Synology DSM
description:
  - Create or delete storage pools on a Synology DSM device.
  - Configure RAID type and assign disks to pools.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The name of the storage pool.
    type: str
    required: true
  raid_type:
    description:
      - The RAID type for the storage pool.
    type: str
    choices: ['basic', 'jbod', 'raid0', 'raid1', 'raid5', 'raid6', 'raid10', 'shr', 'shr2']
  disks:
    description:
      - List of disk identifiers to include in the pool.
    type: list
    elements: str
  state:
    description:
      - Whether the storage pool should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a SHR storage pool
  stevefulme1.synology_dsm.dsm_storage_pool:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "pool1"
    raid_type: shr
    disks:
      - sata1
      - sata2
    state: present

- name: Remove a storage pool
  stevefulme1.synology_dsm.dsm_storage_pool:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "pool1"
    state: absent
'''

RETURN = r'''
storage_pool:
  description: Details about the managed storage pool.
  returned: always
  type: dict
  contains:
    name:
      description: The pool name.
      type: str
      returned: always
    state:
      description: The resulting state.
      type: str
      returned: always
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_pool(client, name):
    """Find a storage pool by name."""
    data = client.request('SYNO.Core.Storage.Pool', 'list', version=1)
    for pool in data.get('pools', []):
        if pool.get('name') == name or pool.get('id') == name:
            return pool
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        raid_type=dict(
            type='str',
            choices=['basic', 'jbod', 'raid0', 'raid1', 'raid5',
                     'raid6', 'raid10', 'shr', 'shr2'],
        ),
        disks=dict(type='list', elements='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['raid_type', 'disks']),
        ],
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        existing = find_pool(client, name)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Storage.Pool', 'create', version=1,
                        extra_params={
                            'name': name,
                            'raid_type': module.params['raid_type'],
                            'disks': json.dumps(module.params['disks']),
                        },
                    )
        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    pool_id = existing.get('id', name)
                    client.request(
                        'SYNO.Core.Storage.Pool', 'delete', version=1,
                        extra_params={'id': str(pool_id)},
                    )
    except DSMError as e:
        module.fail_json(msg='Storage pool operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, storage_pool=result)


if __name__ == '__main__':
    main()
