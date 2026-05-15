#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_hyper_backup
short_description: Manage Hyper Backup tasks on Synology DSM
description:
  - Create, delete, start, and stop Hyper Backup tasks.
  - Returns task info when the task already exists with state=present.
version_added: "0.2.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The Hyper Backup task name.
    type: str
    required: true
  state:
    description:
      - Desired state of the backup task.
    type: str
    choices: ['present', 'absent', 'started', 'stopped']
    default: present
  target_type:
    description:
      - Backup destination type. Required when creating a new task.
    type: str
    choices: ['local', 'remote_rsync', 'cloud']
  target_path:
    description:
      - Destination path or URI for the backup.
    type: str
  schedule:
    description:
      - Backup schedule as a dict with time and repeat_days keys.
    type: dict
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a local backup task
  stevefulme1.synology_dsm.dsm_hyper_backup:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "daily-local-backup"
    target_type: "local"
    target_path: "/volume2/Backup"
    state: present

- name: Start a backup task
  stevefulme1.synology_dsm.dsm_hyper_backup:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "daily-local-backup"
    state: started

- name: Stop a running backup task
  stevefulme1.synology_dsm.dsm_hyper_backup:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "daily-local-backup"
    state: stopped

- name: Remove a backup task
  stevefulme1.synology_dsm.dsm_hyper_backup:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "daily-local-backup"
    state: absent
'''

RETURN = r'''
backup_task:
  description: Details about the managed Hyper Backup task.
  returned: always
  type: dict
  contains:
    name:
      description: The backup task name.
      type: str
      returned: always
    state:
      description: The resulting state of the task.
      type: str
      returned: always
    task_id:
      description: The numeric task ID if available.
      type: int
      returned: when present
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_task(client, name):
    """Find a Hyper Backup task by name."""
    data = client.request('SYNO.Backup.Task', 'list', version=1)
    for task in data.get('task_list', []):
        if task.get('name') == name:
            return task
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(
            type='str', default='present',
            choices=['present', 'absent', 'started', 'stopped'],
        ),
        target_type=dict(type='str', choices=['local', 'remote_rsync', 'cloud']),
        target_path=dict(type='str'),
        schedule=dict(type='dict'),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['target_type'], True),
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
                if not module.params.get('target_type'):
                    module.fail_json(msg='target_type is required to create a backup task.')
                changed = True
                if not module.check_mode:
                    create_params = {
                        'name': name,
                        'additional': json.dumps({
                            'target_type': module.params['target_type'],
                            'target_path': module.params.get('target_path', ''),
                        }),
                    }
                    if module.params.get('schedule'):
                        create_params['schedule'] = json.dumps(module.params['schedule'])
                    client.request('SYNO.Backup.Task', 'create', version=1,
                                   extra_params=create_params)
            else:
                result['task_id'] = existing.get('task_id')

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Backup.Task', 'delete', version=1,
                                   extra_params={'task_id': str(existing['task_id'])})

        elif state == 'started':
            if existing is None:
                module.fail_json(msg='Backup task {0} not found.'.format(name))
            if existing.get('status') != 'running':
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Backup.Task', 'start', version=1,
                                   extra_params={'task_id': str(existing['task_id'])})
            result['task_id'] = existing.get('task_id')

        elif state == 'stopped':
            if existing is None:
                module.fail_json(msg='Backup task {0} not found.'.format(name))
            if existing.get('status') == 'running':
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Backup.Task', 'stop', version=1,
                                   extra_params={'task_id': str(existing['task_id'])})
            result['task_id'] = existing.get('task_id')

    except DSMError as e:
        module.fail_json(msg='Hyper Backup operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, backup_task=result)


if __name__ == '__main__':
    main()
