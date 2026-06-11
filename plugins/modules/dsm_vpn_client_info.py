#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_vpn_client_info
short_description: List VPN client connections on Synology DSM
description:
  - Retrieves a list of VPN client connection profiles from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  protocol:
    description:
      - VPN protocol to query. If not specified, queries all protocols.
    type: str
    choices: ['pptp', 'openvpn', 'l2tp']
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all VPN client profiles
  stevefulme1.synology_dsm.dsm_vpn_client_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: List only OpenVPN profiles
  stevefulme1.synology_dsm.dsm_vpn_client_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    protocol: openvpn
  register: result

- name: Display VPN profiles
  ansible.builtin.debug:
    var: result.profiles
'''

RETURN = r'''
profiles:
  description: List of VPN client profiles configured on the DSM device.
  returned: always
  type: list
  elements: dict
  sample:
    - name: "office_vpn"
      protocol: "openvpn"
      server: "vpn.example.com"
      username: "vpnuser"
    - name: "remote_site"
      protocol: "pptp"
      server: "10.0.0.1"
      username: "siteuser"
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


def main():
    argument_spec = dict(
        protocol=dict(type='str', choices=['pptp', 'openvpn', 'l2tp']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    protocol = module.params.get('protocol')
    client = DSMClient(module)
    all_profiles = []

    try:
        client.login()

        if protocol:
            protocols = [protocol]
        else:
            protocols = ['pptp', 'openvpn', 'l2tp']

        for proto in protocols:
            api = PROTOCOL_API_MAP[proto]
            try:
                data = client.request(api, 'list', version=1)
                profiles = data.get('profiles', [])
                for profile in profiles:
                    profile['protocol'] = proto
                all_profiles.extend(profiles)
            except DSMError:
                continue

    except DSMError as e:
        module.fail_json(msg='Failed to list VPN client profiles: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, profiles=all_profiles)


if __name__ == '__main__':
    main()
