#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_ntp
short_description: Configure NTP settings on Synology DSM
description:
  - Configure NTP server and enable or disable time synchronization on a Synology DSM device.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  server:
    description:
      - The NTP server hostname or IP address.
    type: str
    required: true
  enabled:
    description:
      - Whether NTP time synchronization is enabled.
    type: bool
    default: true
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Configure NTP server
  stevefulme1.synology_dsm.dsm_ntp:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    server: "pool.ntp.org"
    enabled: true

- name: Disable NTP synchronization
  stevefulme1.synology_dsm.dsm_ntp:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    server: "pool.ntp.org"
    enabled: false
'''

RETURN = r'''
ntp:
  description: Details about the NTP configuration.
  returned: always
  type: dict
  contains:
    server:
      description: The NTP server.
      type: str
      returned: always
    enabled:
      description: Whether NTP is enabled.
      type: bool
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def get_ntp_config(client):
    """Get current NTP configuration."""
    try:
        data = client.request('SYNO.Core.NTPServer', 'get', version=1)
        return data
    except DSMError:
        return {}


def main():
    argument_spec = dict(
        server=dict(type='str', required=True),
        enabled=dict(type='bool', default=True),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    server = module.params['server']
    enabled = module.params['enabled']

    client = DSMClient(module)
    changed = False
    result = dict(server=server, enabled=enabled)

    try:
        client.login()
        current = get_ntp_config(client)

        needs_update = (
            current.get('server') != server
            or current.get('enabled', True) != enabled
        )

        if needs_update:
            changed = True
            if not module.check_mode:
                client.request(
                    'SYNO.Core.NTPServer', 'set', version=1,
                    extra_params={
                        'server': server,
                        'enabled': str(enabled).lower(),
                    },
                )
    except DSMError as e:
        module.fail_json(msg='NTP configuration failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, ntp=result)


if __name__ == '__main__':
    main()
