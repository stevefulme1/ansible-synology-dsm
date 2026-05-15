#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_snapshot_replication
short_description: Configure snapshot replication on Synology DSM
description:
  - Create, update, or delete snapshot replication tasks on a Synology DSM device.
  - Replicates shared folder snapshots to a remote Synology NAS.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  share:
    description:
      - Name of the shared folder to replicate.
    type: str
    required: true
  target_server:
    description:
      - Hostname or IP of the target Synology NAS.
    type: str
  target_share:
    description:
      - Target shared folder name on the remote NAS.
    type: str
  schedule:
    description:
      - Replication schedule in cron format.
    type: str
  enabled:
    description:
      - Whether the replication task is enabled.
    type: bool
    default: true
  state:
    description:
      - Whether the replication task should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create snapshot replication
  stevefulme1.synology_dsm.dsm_snapshot_replication:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    share: "projects"
    target_server: "192.168.1.200"
    target_share: "projects_replica"
    schedule: "0 2 * * *"
    state: present

- name: Remove replication task
  stevefulme1.synology_dsm.dsm_snapshot_replication:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    share: "projects"
    state: absent
'''

RETURN = r'''
snapshot_replication:
  description: Snapshot replication task configuration.
  returned: always
  type: dict
  contains:
    share:
      description: Shared folder name.
      type: str
      returned: always
    state:
      description: Resulting state.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_replication(client, share):
    """Find a replication task by share name."""
    data = client.request('SYNO.Core.Share.SnapshotReplication', 'list', version=1)
    for task in data.get('tasks', []):
        if task.get('share') == share:
            return task
    return None


def main():
    argument_spec = dict(
        share=dict(type='str', required=True),
        target_server=dict(type='str'),
        target_share=dict(type='str'),
        schedule=dict(type='str'),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['target_server', 'target_share']),
        ],
    )

    share = module.params['share']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(share=share, state=state)

    try:
        client.login()
        existing = find_replication(client, share)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    params = {
                        'share': share,
                        'target_server': module.params['target_server'],
                        'target_share': module.params['target_share'],
                        'enabled': str(module.params['enabled']).lower(),
                    }
                    if module.params.get('schedule'):
                        params['schedule'] = module.params['schedule']
                    client.request('SYNO.Core.Share.SnapshotReplication', 'create',
                                   version=1, extra_params=params)
            else:
                needs_update = (
                    existing.get('target_server') != module.params['target_server']
                    or existing.get('target_share') != module.params['target_share']
                    or existing.get('enabled') != module.params['enabled']
                )
                if module.params.get('schedule') and existing.get('schedule') != module.params['schedule']:
                    needs_update = True

                if needs_update:
                    changed = True
                    if not module.check_mode:
                        params = {
                            'share': share,
                            'target_server': module.params['target_server'],
                            'target_share': module.params['target_share'],
                            'enabled': str(module.params['enabled']).lower(),
                        }
                        if module.params.get('schedule'):
                            params['schedule'] = module.params['schedule']
                        client.request('SYNO.Core.Share.SnapshotReplication', 'set',
                                       version=1, extra_params=params)

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Core.Share.SnapshotReplication', 'delete',
                                   version=1, extra_params={'share': share})

    except DSMError as e:
        module.fail_json(msg='Snapshot replication operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, snapshot_replication=result)


if __name__ == '__main__':
    main()
