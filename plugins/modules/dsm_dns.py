#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_dns
short_description: Configure DNS settings on Synology DSM
description:
  - Configure primary and secondary DNS server settings on a Synology DSM device.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  primary_dns:
    description:
      - The primary DNS server IP address.
    type: str
    required: true
  secondary_dns:
    description:
      - The secondary DNS server IP address.
    type: str
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Configure DNS servers
  stevefulme1.synology_dsm.dsm_dns:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    primary_dns: "8.8.8.8"
    secondary_dns: "8.8.4.4"

- name: Set primary DNS only
  stevefulme1.synology_dsm.dsm_dns:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    primary_dns: "1.1.1.1"
'''

RETURN = r'''
dns:
  description: Details about the DNS configuration.
  returned: always
  type: dict
  contains:
    primary_dns:
      description: The primary DNS server.
      type: str
      returned: always
    secondary_dns:
      description: The secondary DNS server.
      type: str
      returned: when set
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def get_dns_config(client):
    """Get current DNS configuration."""
    try:
        data = client.request('SYNO.Core.Network', 'get', version=1)
        return data
    except DSMError:
        return {}


def main():
    argument_spec = dict(
        primary_dns=dict(type='str', required=True),
        secondary_dns=dict(type='str'),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    primary_dns = module.params['primary_dns']
    secondary_dns = module.params.get('secondary_dns', '')

    client = DSMClient(module)
    changed = False
    result = dict(primary_dns=primary_dns)
    if secondary_dns:
        result['secondary_dns'] = secondary_dns

    try:
        client.login()
        current = get_dns_config(client)

        needs_update = (
            current.get('dns_primary') != primary_dns
            or current.get('dns_secondary', '') != secondary_dns
        )

        if needs_update:
            changed = True
            if not module.check_mode:
                params = {'dns_primary': primary_dns}
                if secondary_dns:
                    params['dns_secondary'] = secondary_dns
                client.request(
                    'SYNO.Core.Network', 'set', version=1,
                    extra_params=params,
                )
    except DSMError as e:
        module.fail_json(msg='DNS configuration failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, dns=result)


if __name__ == '__main__':
    main()
