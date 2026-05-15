#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_auto_block
short_description: Configure auto-block on Synology DSM
description:
  - Configure the auto-block (fail2ban-like) feature on a Synology DSM device.
  - Blocks IP addresses after repeated failed login attempts.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  enabled:
    description:
      - Whether auto-block is enabled.
    type: bool
    required: true
  attempts:
    description:
      - Number of failed attempts before blocking.
    type: int
    default: 10
  within_minutes:
    description:
      - Time window in minutes for counting failed attempts.
    type: int
    default: 5
  block_days:
    description:
      - Number of days to block the IP. Use 0 for permanent block.
    type: int
    default: 0
  whitelist:
    description:
      - List of IP addresses to exclude from auto-block.
    type: list
    elements: str
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Enable auto-block with defaults
  stevefulme1.synology_dsm.dsm_auto_block:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true

- name: Configure strict auto-block
  stevefulme1.synology_dsm.dsm_auto_block:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true
    attempts: 5
    within_minutes: 3
    block_days: 7
    whitelist:
      - "192.168.1.0/24"

- name: Disable auto-block
  stevefulme1.synology_dsm.dsm_auto_block:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: false
'''

RETURN = r'''
auto_block:
  description: Auto-block configuration.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether auto-block is enabled.
      type: bool
      returned: always
    attempts:
      description: Failed attempts threshold.
      type: int
      returned: always
    within_minutes:
      description: Time window for counting attempts.
      type: int
      returned: always
    block_days:
      description: Block duration in days.
      type: int
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        enabled=dict(type='bool', required=True),
        attempts=dict(type='int', default=10),
        within_minutes=dict(type='int', default=5),
        block_days=dict(type='int', default=0),
        whitelist=dict(type='list', elements='str'),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    client = DSMClient(module)
    changed = False

    try:
        client.login()
        current = client.request('SYNO.Core.Security.AutoBlock', 'get', version=1)

        desired = dict(
            enabled=module.params['enabled'],
            attempts=module.params['attempts'],
            within_minutes=module.params['within_minutes'],
            block_days=module.params['block_days'],
        )

        current_vals = dict(
            enabled=current.get('enable', False),
            attempts=current.get('attempts', 10),
            within_minutes=current.get('within_minutes', 5),
            block_days=current.get('block_days', 0),
        )

        if current_vals != desired:
            changed = True
            if not module.check_mode:
                params = {
                    'enable': str(desired['enabled']).lower(),
                    'attempts': str(desired['attempts']),
                    'within_minutes': str(desired['within_minutes']),
                    'block_days': str(desired['block_days']),
                }
                client.request('SYNO.Core.Security.AutoBlock', 'set', version=1,
                               extra_params=params)

        # Handle whitelist separately if provided
        if module.params.get('whitelist') is not None and module.params['enabled']:
            current_whitelist = current.get('whitelist', [])
            if set(current_whitelist) != set(module.params['whitelist']):
                changed = True
                if not module.check_mode:
                    for ip_addr in module.params['whitelist']:
                        client.request('SYNO.Core.Security.AutoBlock', 'add_whitelist',
                                       version=1, extra_params={'ip': ip_addr})

    except DSMError as e:
        module.fail_json(msg='Failed to configure auto-block: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, auto_block=desired)


if __name__ == '__main__':
    main()
