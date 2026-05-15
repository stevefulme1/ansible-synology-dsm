#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_snapshot
short_description: Manage Btrfs snapshots on Synology DSM
description:
  - Create, delete, and schedule Btrfs snapshots on shared folders.
  - Requires a Btrfs volume on the Synology DSM device.
version_added: "0.2.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  share:
    description:
      - The shared folder name to manage snapshots for.
    type: str
    required: true
  name:
    description:
      - The snapshot name. Required when creating or deleting a snapshot.
    type: str
  schedule:
    description:
      - Snapshot schedule configuration.
    type: dict
    suboptions:
      enabled:
        description:
          - Whether the snapshot schedule is enabled.
        type: bool
        default: false
      frequency:
        description:
          - How often to take scheduled snapshots.
        type: str
        choices: ['daily', 'weekly', 'monthly']
        default: daily
      retention:
        description:
          - Number of scheduled snapshots to retain.
        type: int
        default: 5
  state:
    description:
      - Whether the snapshot should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a snapshot
  stevefulme1.synology_dsm.dsm_snapshot:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    share: "projects"
    name: "before-upgrade"
    state: present

- name: Delete a snapshot
  stevefulme1.synology_dsm.dsm_snapshot:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    share: "projects"
    name: "before-upgrade"
    state: absent

- name: Configure snapshot schedule
  stevefulme1.synology_dsm.dsm_snapshot:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    share: "projects"
    schedule:
      enabled: true
      frequency: daily
      retention: 7
'''

RETURN = r'''
snapshot:
  description: Details about the managed snapshot.
  returned: always
  type: dict
  contains:
    share:
      description: The shared folder name.
      type: str
      returned: always
    name:
      description: The snapshot name.
      type: str
      returned: when applicable
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def list_snapshots(client, share):
    """List all snapshots for a given shared folder."""
    data = client.request(
        'SYNO.Core.Share.Snapshot', 'list', version=1,
        extra_params={'share_name': share},
    )
    return data.get('snapshots', [])


def find_snapshot(client, share, name):
    """Find a snapshot by name."""
    for snap in list_snapshots(client, share):
        if snap.get('desc') == name or snap.get('name') == name:
            return snap
    return None


def main():
    schedule_spec = dict(
        enabled=dict(type='bool', default=False),
        frequency=dict(type='str', default='daily', choices=['daily', 'weekly', 'monthly']),
        retention=dict(type='int', default=5),
    )

    argument_spec = dict(
        share=dict(type='str', required=True),
        name=dict(type='str'),
        schedule=dict(type='dict', options=schedule_spec),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'absent', ['name']),
        ],
    )

    share = module.params['share']
    name = module.params.get('name')
    schedule = module.params.get('schedule')
    state = module.params['state']

    client = DSMClient(module)
    result = dict(share=share, name=name)
    changed = False

    try:
        client.login()

        if state == 'present' and name:
            existing = find_snapshot(client, share, name)
            if existing is None:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Share.Snapshot', 'create', version=1,
                        extra_params={
                            'share_name': share,
                            'desc': name,
                            'is_lock': 'false',
                        },
                    )

        elif state == 'present' and schedule:
            sched_params = {
                'share_name': share,
                'additional': json.dumps({
                    'enable_schedule': schedule.get('enabled', False),
                    'schedule_plan': schedule.get('frequency', 'daily'),
                    'max_snap_count': schedule.get('retention', 5),
                }),
            }
            changed = True
            if not module.check_mode:
                client.request(
                    'SYNO.Core.Share.Snapshot', 'set', version=1,
                    extra_params=sched_params,
                )

        elif state == 'absent':
            existing = find_snapshot(client, share, name)
            if existing is not None:
                changed = True
                if not module.check_mode:
                    snap_id = existing.get('id', existing.get('name'))
                    client.request(
                        'SYNO.Core.Share.Snapshot', 'delete', version=1,
                        extra_params={
                            'share_name': share,
                            'snapshots': json.dumps([snap_id]),
                        },
                    )

    except DSMError as e:
        module.fail_json(msg='Snapshot operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, snapshot=result)


if __name__ == '__main__':
    main()
