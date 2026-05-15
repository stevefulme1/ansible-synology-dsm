#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_snmp
short_description: Configure SNMP on Synology DSM
description:
  - Configure SNMP service settings on a Synology DSM device.
  - Supports SNMPv1/v2c and SNMPv3 configuration.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  enabled:
    description:
      - Whether SNMP is enabled.
    type: bool
    default: true
  community:
    description:
      - The SNMP community string for v1/v2c.
    type: str
    default: public
  version:
    description:
      - The SNMP version to use.
    type: str
    choices: ['v1v2c', 'v3']
    default: v1v2c
  state:
    description:
      - Whether SNMP should be enabled or disabled.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Enable SNMP with custom community
  stevefulme1.synology_dsm.dsm_snmp:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true
    community: "mynetwork"
    version: v1v2c
    state: present

- name: Disable SNMP
  stevefulme1.synology_dsm.dsm_snmp:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    state: absent
'''

RETURN = r'''
snmp:
  description: Details about the SNMP configuration.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether SNMP is enabled.
      type: bool
      returned: always
    state:
      description: The resulting state.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def get_snmp_config(client):
    """Get current SNMP configuration."""
    try:
        data = client.request('SYNO.Core.SNMP', 'get', version=1)
        return data
    except DSMError:
        return {}


def main():
    argument_spec = dict(
        enabled=dict(type='bool', default=True),
        community=dict(type='str', default='public'),
        version=dict(type='str', default='v1v2c', choices=['v1v2c', 'v3']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(enabled=state == 'present', state=state)

    try:
        client.login()
        current = get_snmp_config(client)

        if state == 'present':
            needs_update = (
                not current.get('snmpEnable', False)
                or current.get('community') != module.params['community']
            )
            if needs_update:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.SNMP', 'set', version=1,
                        extra_params={
                            'snmpEnable': 'true',
                            'community': module.params['community'],
                            'version': module.params['version'],
                        },
                    )
        elif state == 'absent':
            if current.get('snmpEnable', False):
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.SNMP', 'set', version=1,
                        extra_params={'snmpEnable': 'false'},
                    )
    except DSMError as e:
        module.fail_json(msg='SNMP configuration failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, snmp=result)


if __name__ == '__main__':
    main()
