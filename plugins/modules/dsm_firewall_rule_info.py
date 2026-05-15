#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_firewall_rule_info
short_description: List firewall rules on Synology DSM
description:
  - Retrieves all configured firewall rules from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all firewall rules
  stevefulme1.synology_dsm.dsm_firewall_rule_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display rules
  ansible.builtin.debug:
    var: result.firewall_rules
'''

RETURN = r'''
firewall_rules:
  description: List of configured firewall rules.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Rule description or name.
      type: str
      returned: always
    action:
      description: Whether traffic is allowed or denied.
      type: str
      returned: always
    enabled:
      description: Whether the rule is active.
      type: bool
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
        data = client.request('SYNO.Core.Security.Firewall.Rules', 'get', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to retrieve firewall rules: {0}'.format(str(e)))
    finally:
        client.logout()

    rules = []
    for rule in data.get('rules', []):
        rules.append(dict(
            name=rule.get('name', rule.get('desc', '')),
            action=rule.get('action', ''),
            enabled=rule.get('enabled', False),
        ))

    module.exit_json(changed=False, firewall_rules=rules)


if __name__ == '__main__':
    main()
