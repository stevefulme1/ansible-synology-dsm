#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_cloud_sync
short_description: Manage Cloud Sync tasks on Synology DSM
description:
  - Create, update, or delete Cloud Sync tasks on a Synology DSM device.
  - Requires the Cloud Sync package to be installed.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The Cloud Sync task name.
    type: str
    required: true
  cloud_type:
    description:
      - The cloud provider type.
    type: str
    choices: ['s3', 'azure', 'google', 'dropbox', 'onedrive', 'backblaze']
  direction:
    description:
      - The sync direction.
    type: str
    choices: ['download', 'upload', 'bidirectional']
    default: bidirectional
  local_path:
    description:
      - Local folder path on the NAS.
    type: str
  remote_path:
    description:
      - Remote folder path in the cloud.
    type: str
  schedule:
    description:
      - Sync schedule configuration.
    type: dict
    suboptions:
      enabled:
        description:
          - Whether the schedule is enabled.
        type: bool
        default: true
      interval:
        description:
          - Sync interval in minutes.
        type: int
        default: 60
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
- name: Create an S3 Cloud Sync task
  stevefulme1.synology_dsm.dsm_cloud_sync:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "s3-backup"
    cloud_type: s3
    direction: upload
    local_path: "/volume1/backups"
    remote_path: "/nas-backups"
    state: present

- name: Remove a Cloud Sync task
  stevefulme1.synology_dsm.dsm_cloud_sync:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "s3-backup"
    state: absent
'''

RETURN = r'''
cloud_sync:
  description: Details about the managed Cloud Sync task.
  returned: always
  type: dict
  contains:
    name:
      description: The task name.
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


def find_task(client, name):
    """Find a Cloud Sync task by name."""
    data = client.request('SYNO.CloudSync.Task', 'list', version=1)
    for task in data.get('tasks', data.get('data', {}).get('tasks', [])):
        if task.get('name') == name:
            return task
    return None


def main():
    schedule_spec = dict(
        enabled=dict(type='bool', default=True),
        interval=dict(type='int', default=60),
    )

    argument_spec = dict(
        name=dict(type='str', required=True),
        cloud_type=dict(
            type='str',
            choices=['s3', 'azure', 'google', 'dropbox', 'onedrive', 'backblaze'],
        ),
        direction=dict(
            type='str', default='bidirectional',
            choices=['download', 'upload', 'bidirectional'],
        ),
        local_path=dict(type='str'),
        remote_path=dict(type='str'),
        schedule=dict(type='dict', options=schedule_spec),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['cloud_type', 'local_path', 'remote_path']),
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
                        'cloud_type': module.params['cloud_type'],
                        'direction': module.params['direction'],
                        'local_path': module.params['local_path'],
                        'remote_path': module.params['remote_path'],
                    }
                    schedule = module.params.get('schedule')
                    if schedule:
                        params['schedule'] = json.dumps(schedule)
                    client.request(
                        'SYNO.CloudSync.Task', 'create', version=1,
                        extra_params=params,
                    )
        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    task_id = existing.get('id', existing.get('task_id'))
                    client.request(
                        'SYNO.CloudSync.Task', 'delete', version=1,
                        extra_params={'id': str(task_id)},
                    )
    except DSMError as e:
        module.fail_json(msg='Cloud Sync operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, cloud_sync=result)


if __name__ == '__main__':
    main()
