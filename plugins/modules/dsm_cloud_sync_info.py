#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_cloud_sync_info
short_description: List Cloud Sync tasks on Synology DSM
description:
  - Retrieves a list of Cloud Sync connection tasks from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List Cloud Sync tasks
  stevefulme1.synology_dsm.dsm_cloud_sync_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display cloud sync connections
  ansible.builtin.debug:
    var: result.cloud_sync_tasks
'''

RETURN = r'''
cloud_sync_tasks:
  description: List of Cloud Sync tasks.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Task name.
      type: str
      returned: always
    cloud_type:
      description: Cloud provider type.
      type: str
      returned: always
    status:
      description: Sync status.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    module = AnsibleModule(
        argument_spec=dsm_argument_spec,
        supports_check_mode=True,
    )

    client = DSMClient(module)

    try:
        client.login()
        data = client.request('SYNO.CloudSync.Task', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list Cloud Sync tasks: {0}'.format(str(e)))
    finally:
        client.logout()

    tasks = []
    for task in data.get('tasks', []):
        tasks.append(dict(
            name=task.get('name', ''),
            cloud_type=task.get('cloud_type', ''),
            status=task.get('status', ''),
        ))

    module.exit_json(changed=False, cloud_sync_tasks=tasks)


if __name__ == '__main__':
    main()
