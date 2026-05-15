#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_firewall_rule
short_description: Manage firewall rules on Synology DSM
description:
  - Create, update, or delete firewall rules on a Synology DSM device.
version_added: "0.2.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - A descriptive name for the firewall rule.
    type: str
    required: true
  ports:
    description:
      - List of port/protocol definitions for this rule.
    type: list
    elements: dict
    suboptions:
      port:
        description:
          - Port number or range (e.g. 80, 443, 8000-9000).
        type: str
        required: true
      protocol:
        description:
          - Network protocol.
        type: str
        choices: ['tcp', 'udp', 'tcp/udp']
        default: tcp
  source_ip:
    description:
      - Source IP address or CIDR range.
    type: str
    default: 0.0.0.0/0
  action:
    description:
      - Whether to allow or deny matching traffic.
    type: str
    choices: ['allow', 'deny']
    default: allow
  direction:
    description:
      - Traffic direction for the rule.
    type: str
    choices: ['inbound']
    default: inbound
  enabled:
    description:
      - Whether the firewall rule is enabled.
    type: bool
    default: true
  state:
    description:
      - Whether the firewall rule should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Allow HTTPS traffic
  stevefulme1.synology_dsm.dsm_firewall_rule:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "Allow HTTPS"
    ports:
      - port: "443"
        protocol: tcp
    source_ip: "0.0.0.0/0"
    action: allow
    state: present

- name: Deny all from a subnet
  stevefulme1.synology_dsm.dsm_firewall_rule:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "Block guest network"
    source_ip: "10.0.0.0/8"
    action: deny
    state: present

- name: Remove a firewall rule
  stevefulme1.synology_dsm.dsm_firewall_rule:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "Allow HTTPS"
    state: absent
'''

RETURN = r'''
firewall_rule:
  description: Details about the managed firewall rule.
  returned: always
  type: dict
  contains:
    name:
      description: The rule description.
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


def get_firewall_rules(client):
    """Get all firewall rules."""
    data = client.request(
        'SYNO.Core.Security.Firewall.Rules', 'get', version=1,
    )
    return data.get('rules', [])


def find_rule(rules, name):
    """Find a rule by its description/name field."""
    for rule in rules:
        if rule.get('name') == name or rule.get('desc') == name:
            return rule
    return None


def build_rule_payload(module):
    """Build the rule payload from module params."""
    ports_param = module.params.get('ports') or []
    ports = []
    for p in ports_param:
        ports.append({
            'port': p.get('port', ''),
            'protocol': p.get('protocol', 'tcp'),
        })

    return {
        'name': module.params['name'],
        'src_ip': module.params.get('source_ip', '0.0.0.0/0'),
        'ports': ports,
        'action': module.params['action'],
        'direction': module.params['direction'],
        'enabled': module.params['enabled'],
    }


def main():
    port_spec = dict(
        port=dict(type='str', required=True),
        protocol=dict(type='str', default='tcp', choices=['tcp', 'udp', 'tcp/udp']),
    )

    argument_spec = dict(
        name=dict(type='str', required=True),
        ports=dict(type='list', elements='dict', options=port_spec),
        source_ip=dict(type='str', default='0.0.0.0/0'),
        action=dict(type='str', default='allow', choices=['allow', 'deny']),
        direction=dict(type='str', default='inbound', choices=['inbound']),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        rules = get_firewall_rules(client)
        existing = find_rule(rules, name)

        if state == 'present':
            payload = build_rule_payload(module)
            if existing is None:
                changed = True
                if not module.check_mode:
                    rules.append(payload)
                    client.request(
                        'SYNO.Core.Security.Firewall.Rules', 'set', version=1,
                        extra_params={'rules': json.dumps(rules)},
                    )
            else:
                # Check for differences
                needs_update = False
                for key in ('src_ip', 'action', 'enabled'):
                    if existing.get(key) != payload.get(key):
                        needs_update = True
                        break
                if not needs_update and existing.get('ports') != payload.get('ports'):
                    needs_update = True

                if needs_update:
                    changed = True
                    if not module.check_mode:
                        updated_rules = [payload if find_rule([r], name) else r for r in rules]
                        client.request(
                            'SYNO.Core.Security.Firewall.Rules', 'set', version=1,
                            extra_params={'rules': json.dumps(updated_rules)},
                        )

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    updated_rules = [r for r in rules if not find_rule([r], name)]
                    client.request(
                        'SYNO.Core.Security.Firewall.Rules', 'set', version=1,
                        extra_params={'rules': json.dumps(updated_rules)},
                    )

    except DSMError as e:
        module.fail_json(msg='Firewall rule operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, firewall_rule=result)


if __name__ == '__main__':
    main()
