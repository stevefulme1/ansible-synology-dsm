#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_log_info
short_description: Query system logs on Synology DSM
description:
  - Retrieves system log entries from a Synology DSM device.
  - Supports filtering by log level and pagination.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  limit:
    description:
      - Maximum number of log entries to return.
    type: int
    default: 50
  offset:
    description:
      - Offset for pagination.
    type: int
    default: 0
  level:
    description:
      - Filter logs by severity level.
    type: str
    choices: ['info', 'warn', 'err']
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get recent system logs
  stevefulme1.synology_dsm.dsm_log_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    limit: 100
  register: result

- name: Get error logs only
  stevefulme1.synology_dsm.dsm_log_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    level: err
    limit: 20
'''

RETURN = r'''
logs:
  description: List of system log entries.
  returned: always
  type: list
  elements: dict
  contains:
    time:
      description: Log entry timestamp.
      type: str
      returned: always
    level:
      description: Log severity level.
      type: str
      returned: always
    message:
      description: Log message.
      type: str
      returned: always
total:
  description: Total number of log entries matching the filter.
  returned: always
  type: int
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        limit=dict(type='int', default=50),
        offset=dict(type='int', default=0),
        level=dict(type='str', choices=['info', 'warn', 'err']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    client = DSMClient(module)

    try:
        client.login()
        params = {
            'limit': str(module.params['limit']),
            'offset': str(module.params['offset']),
        }
        if module.params.get('level'):
            params['level'] = module.params['level']

        data = client.request('SYNO.Core.SyslogClient.Log', 'list', version=1,
                              extra_params=params)
    except DSMError as e:
        module.fail_json(msg='Failed to query system logs: {0}'.format(str(e)))
    finally:
        client.logout()

    logs = []
    for entry in data.get('logs', []):
        logs.append(dict(
            time=entry.get('time', ''),
            level=entry.get('level', ''),
            message=entry.get('msg', ''),
        ))

    module.exit_json(changed=False, logs=logs, total=data.get('total', 0))


if __name__ == '__main__':
    main()
