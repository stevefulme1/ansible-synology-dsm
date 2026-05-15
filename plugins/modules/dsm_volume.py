#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_volume
short_description: Manage volumes on Synology DSM
description:
  - Create or delete volumes on a Synology DSM device.
  - Volumes are created on existing storage pools.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The volume name or path (e.g. volume1).
    type: str
    required: true
  pool:
    description:
      - The storage pool name or ID to create the volume on.
    type: str
  size:
    description:
      - Volume size in GB. Use 0 or omit for maximum available.
    type: int
  filesystem:
    description:
      - The filesystem type for the volume.
    type: str
    choices: ['btrfs', 'ext4']
    default: btrfs
  state:
    description:
      - Whether the volume should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a Btrfs volume
  stevefulme1.synology_dsm.dsm_volume:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "volume1"
    pool: "pool1"
    size: 500
    filesystem: btrfs
    state: present

- name: Remove a volume
  stevefulme1.synology_dsm.dsm_volume:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "volume1"
    state: absent
'''

RETURN = r'''
volume:
  description: Details about the managed volume.
  returned: always
  type: dict
  contains:
    name:
      description: The volume name.
      type: str
      returned: always
    state:
      description: The resulting state.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_volume(client, name):
    """Find a volume by name."""
    data = client.request('SYNO.Core.Storage.Volume', 'list', version=1)
    for vol in data.get('volumes', []):
        vol_name = vol.get('display_name', vol.get('vol_path', ''))
        if name in (vol_name, vol.get('id', ''), vol.get('vol_path', '')):
            return vol
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        pool=dict(type='str'),
        size=dict(type='int'),
        filesystem=dict(type='str', default='btrfs', choices=['btrfs', 'ext4']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['pool']),
        ],
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        existing = find_volume(client, name)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    params = {
                        'name': name,
                        'pool_id': module.params['pool'],
                        'filesystem': module.params['filesystem'],
                    }
                    if module.params.get('size'):
                        params['size'] = str(module.params['size'])
                    client.request(
                        'SYNO.Core.Storage.Volume', 'create', version=1,
                        extra_params=params,
                    )
        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    vol_id = existing.get('id', name)
                    client.request(
                        'SYNO.Core.Storage.Volume', 'delete', version=1,
                        extra_params={'id': str(vol_id)},
                    )
    except DSMError as e:
        module.fail_json(msg='Volume operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, volume=result)


if __name__ == '__main__':
    main()
