#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_auto_block_info
short_description: Get auto-block configuration on Synology DSM
description:
  - Retrieves auto-block (fail2ban-like) configuration from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get auto-block configuration
  stevefulme1.synology_dsm.dsm_auto_block_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display auto-block configuration
  ansible.builtin.debug:
    var: result.auto_block
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
      description: Number of failed attempts before blocking.
      type: int
      returned: always
    within_minutes:
      description: Time window in minutes for counting failed attempts.
      type: int
      returned: always
    block_days:
      description: Number of days to block the IP (0 for permanent).
      type: int
      returned: always
    whitelist:
      description: List of IP addresses excluded from auto-block.
      type: list
      elements: str
      returned: always
  sample:
    enabled: true
    attempts: 10
    within_minutes: 5
    block_days: 0
    whitelist:
      - "192.168.1.0/24"
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
        data = client.request('SYNO.Core.Security.AutoBlock', 'get', version=1)

        auto_block = {
            'enabled': data.get('enable', False),
            'attempts': data.get('attempts', 10),
            'within_minutes': data.get('within_minutes', 5),
            'block_days': data.get('block_days', 0),
            'whitelist': data.get('whitelist', []),
        }
    except DSMError as e:
        module.fail_json(msg='Failed to get auto-block configuration: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, auto_block=auto_block)


if __name__ == '__main__':
    main()
