#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_task_scheduler
short_description: Manage scheduled tasks on Synology DSM
description:
  - Create, update, or delete scheduled tasks on a Synology DSM device.
  - Supports script execution and recycle bin emptying tasks.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the scheduled task.
    type: str
    required: true
  type:
    description:
      - Type of scheduled task.
    type: str
    choices: ['script', 'recycle_bin']
    default: script
  schedule:
    description:
      - Schedule in cron format.
    type: str
  script_path:
    description:
      - Path to the script to execute. Required when type is script.
    type: str
  enabled:
    description:
      - Whether the scheduled task is enabled.
    type: bool
    default: true
  state:
    description:
      - Whether the task should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a scheduled script task
  stevefulme1.synology_dsm.dsm_task_scheduler:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "daily_cleanup"
    type: script
    script_path: "/volume1/scripts/cleanup.sh"
    schedule: "0 3 * * *"
    state: present

- name: Create recycle bin task
  stevefulme1.synology_dsm.dsm_task_scheduler:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "empty_recycle_bin"
    type: recycle_bin
    schedule: "0 4 * * 0"
    state: present

- name: Remove a scheduled task
  stevefulme1.synology_dsm.dsm_task_scheduler:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "daily_cleanup"
    state: absent
'''

RETURN = r'''
task:
  description: Scheduled task configuration.
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
    """Find a scheduled task by name."""
    data = client.request('SYNO.Core.TaskScheduler', 'list', version=2)
    for task in data.get('tasks', []):
        if task.get('name') == name:
            return task
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        type=dict(type='str', default='script', choices=['script', 'recycle_bin']),
        schedule=dict(type='str'),
        script_path=dict(type='str'),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['schedule']),
            ('type', 'script', ['script_path'], True),
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
            task_info = {
                'name': name,
                'type': module.params['type'],
                'schedule': module.params.get('schedule', ''),
                'enabled': module.params['enabled'],
            }
            if module.params['type'] == 'script' and module.params.get('script_path'):
                task_info['script_path'] = module.params['script_path']

            if existing is None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Core.TaskScheduler', 'create', version=2,
                                   extra_params={'task': json.dumps(task_info)})
            else:
                needs_update = (
                    existing.get('schedule') != module.params.get('schedule', '')
                    or existing.get('enabled') != module.params['enabled']
                )
                if module.params['type'] == 'script':
                    if existing.get('script_path') != module.params.get('script_path'):
                        needs_update = True

                if needs_update:
                    changed = True
                    if not module.check_mode:
                        task_info['id'] = existing.get('id')
                        client.request('SYNO.Core.TaskScheduler', 'set', version=2,
                                       extra_params={'task': json.dumps(task_info)})

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Core.TaskScheduler', 'delete', version=2,
                                   extra_params={'id': json.dumps([existing.get('id')])})

    except DSMError as e:
        module.fail_json(msg='Task scheduler operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, task=result)


if __name__ == '__main__':
    main()
