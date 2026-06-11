#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_task_scheduler_info
short_description: List scheduled tasks on Synology DSM
description:
  - Retrieves a list of scheduled tasks from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all scheduled tasks
  stevefulme1.synology_dsm.dsm_task_scheduler_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display scheduled tasks
  ansible.builtin.debug:
    var: result.tasks
'''

RETURN = r'''
tasks:
  description: List of scheduled tasks configured on the DSM device.
  returned: always
  type: list
  elements: dict
  sample:
    - id: "1"
      name: "daily_cleanup"
      type: "script"
      schedule: "0 3 * * *"
      enabled: true
      script_path: "/volume1/scripts/cleanup.sh"
    - id: "2"
      name: "empty_recycle_bin"
      type: "recycle_bin"
      schedule: "0 4 * * 0"
      enabled: true
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
        data = client.request('SYNO.Core.TaskScheduler', 'list', version=2)
    except DSMError as e:
        module.fail_json(msg='Failed to list scheduled tasks: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, tasks=data.get('tasks', []))


if __name__ == '__main__':
    main()
