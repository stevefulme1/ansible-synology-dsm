#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_dns_info
short_description: Get DNS configuration on Synology DSM
description:
  - Retrieves DNS server configuration from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get DNS configuration
  stevefulme1.synology_dsm.dsm_dns_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display DNS servers
  ansible.builtin.debug:
    var: result.dns
'''

RETURN = r'''
dns:
  description: DNS configuration.
  returned: always
  type: dict
  contains:
    primary_dns:
      description: Primary DNS server IP address.
      type: str
      returned: always
    secondary_dns:
      description: Secondary DNS server IP address.
      type: str
      returned: when configured
  sample:
    primary_dns: "8.8.8.8"
    secondary_dns: "8.8.4.4"
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
        data = client.request('SYNO.Core.Network', 'get', version=1)

        dns = {
            'primary_dns': data.get('dns_primary', ''),
        }
        if data.get('dns_secondary'):
            dns['secondary_dns'] = data['dns_secondary']
    except DSMError as e:
        module.fail_json(msg='Failed to get DNS configuration: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, dns=dns)


if __name__ == '__main__':
    main()
