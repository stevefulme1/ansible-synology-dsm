#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_network
short_description: Configure network interfaces on Synology DSM
description:
  - Read and update network interface settings on a Synology DSM device.
  - Only applies changes when the desired configuration differs from current.
version_added: "0.2.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The network interface name (e.g. eth0, bond0, ovs_eth0).
    type: str
    required: true
  ip_address:
    description:
      - Static IPv4 address to assign to the interface.
    type: str
  subnet_mask:
    description:
      - Subnet mask for the interface.
    type: str
  gateway:
    description:
      - Default gateway address.
    type: str
  dns_servers:
    description:
      - List of DNS server addresses.
    type: list
    elements: str
  mtu:
    description:
      - Maximum transmission unit for the interface.
    type: int
  state:
    description:
      - Desired state of the network interface configuration.
    type: str
    choices: ['present']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Configure a static IP on eth0
  stevefulme1.synology_dsm.dsm_network:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "eth0"
    ip_address: "192.168.1.50"
    subnet_mask: "255.255.255.0"
    gateway: "192.168.1.1"
    dns_servers:
      - "8.8.8.8"
      - "8.8.4.4"
    mtu: 1500

- name: Update DNS only
  stevefulme1.synology_dsm.dsm_network:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "eth0"
    dns_servers:
      - "1.1.1.1"
      - "1.0.0.1"
'''

RETURN = r'''
network:
  description: Details about the network interface configuration.
  returned: always
  type: dict
  contains:
    name:
      description: The interface name.
      type: str
      returned: always
    changed_fields:
      description: List of fields that were modified.
      type: list
      returned: when changed
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def get_interface_config(client, name):
    """Get current configuration for a network interface."""
    data = client.request('SYNO.Core.Network', 'get', version=1)
    for iface in data.get('interfaces', []):
        if iface.get('id') == name or iface.get('name') == name:
            return iface
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        ip_address=dict(type='str'),
        subnet_mask=dict(type='str'),
        gateway=dict(type='str'),
        dns_servers=dict(type='list', elements='str'),
        mtu=dict(type='int'),
        state=dict(type='str', default='present', choices=['present']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']

    client = DSMClient(module)
    changed = False
    changed_fields = []
    result = dict(name=name)

    try:
        client.login()
        current = get_interface_config(client, name)

        if current is None:
            module.fail_json(msg='Network interface {0} not found.'.format(name))

        update_params = {}
        field_map = {
            'ip_address': 'ip',
            'subnet_mask': 'netmask',
            'gateway': 'gateway',
            'mtu': 'mtu',
        }

        for param_name, api_key in field_map.items():
            desired = module.params.get(param_name)
            if desired is not None:
                current_val = current.get(api_key)
                if param_name == 'mtu':
                    current_val = int(current_val) if current_val else None
                if str(desired) != str(current_val) if current_val else True:
                    update_params[api_key] = desired
                    changed_fields.append(param_name)

        if module.params.get('dns_servers') is not None:
            desired_dns = module.params['dns_servers']
            current_dns = current.get('dns', [])
            if desired_dns != current_dns:
                update_params['dns'] = desired_dns
                changed_fields.append('dns_servers')

        if update_params:
            changed = True
            if not module.check_mode:
                update_params['id'] = name
                client.request(
                    'SYNO.Core.Network', 'set', version=1,
                    extra_params={
                        'additional': json.dumps(update_params),
                    },
                )

        result['changed_fields'] = changed_fields

    except DSMError as e:
        module.fail_json(msg='Network configuration failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, network=result)


if __name__ == '__main__':
    main()
