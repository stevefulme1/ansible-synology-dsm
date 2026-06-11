#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_proxy_info
short_description: Get proxy configuration on Synology DSM
description:
  - Retrieves HTTP proxy configuration from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get proxy configuration
  stevefulme1.synology_dsm.dsm_proxy_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display proxy configuration
  ansible.builtin.debug:
    var: result.proxy
'''

RETURN = r'''
proxy:
  description: Proxy configuration.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether proxy is enabled.
      type: bool
      returned: always
    server:
      description: Proxy server hostname or IP address.
      type: str
      returned: when enabled
    port:
      description: Proxy server port.
      type: int
      returned: when enabled
    username:
      description: Proxy authentication username.
      type: str
      returned: when configured
  sample:
    enabled: true
    server: "proxy.example.com"
    port: 8080
    username: "proxyuser"
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
        data = client.request('SYNO.Core.Network.Proxy', 'get', version=1)

        proxy = {
            'enabled': data.get('enabled', False),
        }
        if data.get('server'):
            proxy['server'] = data['server']
        if data.get('port'):
            proxy['port'] = data['port']
        if data.get('username'):
            proxy['username'] = data['username']
    except DSMError as e:
        module.fail_json(msg='Failed to get proxy configuration: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, proxy=proxy)


if __name__ == '__main__':
    main()
