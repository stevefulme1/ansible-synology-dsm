#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_hyper_backup_info
short_description: List Hyper Backup tasks on Synology DSM
description:
  - Retrieves a list of Hyper Backup tasks from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List Hyper Backup tasks
  stevefulme1.synology_dsm.dsm_hyper_backup_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display backup tasks
  ansible.builtin.debug:
    var: result.hyper_backup_tasks
'''

RETURN = r'''
hyper_backup_tasks:
  description: List of Hyper Backup tasks.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Backup task name.
      type: str
      returned: always
    status:
      description: Current task status.
      type: str
      returned: always
    last_backup:
      description: Timestamp of last backup.
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
        data = client.request('SYNO.Backup.Task', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list Hyper Backup tasks: {0}'.format(str(e)))
    finally:
        client.logout()

    tasks = []
    for task in data.get('tasks', []):
        tasks.append(dict(
            name=task.get('name', ''),
            status=task.get('status', ''),
            last_backup=task.get('last_bkp_time', ''),
        ))

    module.exit_json(changed=False, hyper_backup_tasks=tasks)


if __name__ == '__main__':
    main()
