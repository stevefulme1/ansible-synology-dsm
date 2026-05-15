#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_network_info
short_description: List network interfaces on Synology DSM
description:
  - Retrieves a list of network interfaces from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List network interfaces
  stevefulme1.synology_dsm.dsm_network_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display interfaces
  ansible.builtin.debug:
    var: result.network_interfaces
'''

RETURN = r'''
network_interfaces:
  description: List of network interfaces.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Interface name.
      type: str
      returned: always
    ip:
      description: IP address.
      type: str
      returned: always
    mac:
      description: MAC address.
      type: str
      returned: always
    status:
      description: Link status.
      type: str
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
        data = client.request('SYNO.Core.Network', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list network interfaces: {0}'.format(str(e)))
    finally:
        client.logout()

    interfaces = []
    for iface in data.get('interfaces', []):
        interfaces.append(dict(
            name=iface.get('name', ''),
            ip=iface.get('ip', ''),
            mac=iface.get('mac', ''),
            status=iface.get('status', ''),
        ))

    module.exit_json(changed=False, network_interfaces=interfaces)


if __name__ == '__main__':
    main()
