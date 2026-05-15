#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_vpn_client
short_description: Manage VPN client connections on Synology DSM
description:
  - Create, update, or delete VPN client connection profiles on a Synology DSM device.
  - Supports PPTP, OpenVPN, and L2TP protocols.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the VPN connection profile.
    type: str
    required: true
  protocol:
    description:
      - VPN protocol to use.
    type: str
    choices: ['pptp', 'openvpn', 'l2tp']
    default: openvpn
  server:
    description:
      - VPN server hostname or IP address.
    type: str
  username:
    description:
      - VPN authentication username.
    type: str
  password:
    description:
      - VPN authentication password.
    type: str
  state:
    description:
      - Whether the VPN profile should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create OpenVPN connection
  stevefulme1.synology_dsm.dsm_vpn_client:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "office_vpn"
    protocol: openvpn
    server: "vpn.example.com"
    username: "vpnuser"
    password: "vpnpass"
    state: present

- name: Remove VPN profile
  stevefulme1.synology_dsm.dsm_vpn_client:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "office_vpn"
    state: absent
'''

RETURN = r'''
vpn_client:
  description: VPN client profile configuration.
  returned: always
  type: dict
  contains:
    name:
      description: Profile name.
      type: str
      returned: always
    protocol:
      description: VPN protocol.
      type: str
      returned: always
    state:
      description: Resulting state.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)

PROTOCOL_API_MAP = {
    'pptp': 'SYNO.Core.Network.VPN.PPTP',
    'openvpn': 'SYNO.Core.Network.VPN.OpenVPN',
    'l2tp': 'SYNO.Core.Network.VPN.L2TP',
}


def find_profile(client, name, protocol):
    """Find a VPN profile by name."""
    api = PROTOCOL_API_MAP.get(protocol, 'SYNO.Core.Network.VPN.OpenVPN')
    data = client.request(api, 'list', version=1)
    for profile in data.get('profiles', []):
        if profile.get('name') == name:
            return profile
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        protocol=dict(type='str', default='openvpn', choices=['pptp', 'openvpn', 'l2tp']),
        server=dict(type='str'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['server', 'username']),
        ],
    )

    name = module.params['name']
    protocol = module.params['protocol']
    state = module.params['state']
    api = PROTOCOL_API_MAP.get(protocol, 'SYNO.Core.Network.VPN.OpenVPN')

    client = DSMClient(module)
    changed = False
    result = dict(name=name, protocol=protocol, state=state)

    try:
        client.login()
        existing = find_profile(client, name, protocol)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    params = {
                        'name': name,
                        'server': module.params['server'],
                        'username': module.params['username'],
                    }
                    if module.params.get('password'):
                        params['password'] = module.params['password']
                    client.request(api, 'create', version=1, extra_params=params)
            else:
                needs_update = (
                    existing.get('server') != module.params['server']
                    or existing.get('username') != module.params['username']
                )
                if needs_update:
                    changed = True
                    if not module.check_mode:
                        params = {
                            'name': name,
                            'server': module.params['server'],
                            'username': module.params['username'],
                        }
                        if module.params.get('password'):
                            params['password'] = module.params['password']
                        client.request(api, 'set', version=1, extra_params=params)

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    client.request(api, 'delete', version=1,
                                   extra_params={'name': name})

    except DSMError as e:
        module.fail_json(msg='VPN client operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, vpn_client=result)


if __name__ == '__main__':
    main()
