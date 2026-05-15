#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_proxy
short_description: Configure proxy settings on Synology DSM
description:
  - Configure HTTP proxy settings on a Synology DSM device.
  - Supports enabling, disabling, and setting proxy server details.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  enabled:
    description:
      - Whether the proxy is enabled.
    type: bool
    required: true
  server:
    description:
      - Proxy server hostname or IP address.
    type: str
  port:
    description:
      - Proxy server port.
    type: int
    default: 3128
  username:
    description:
      - Proxy authentication username.
    type: str
  password:
    description:
      - Proxy authentication password.
    type: str
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Configure proxy
  stevefulme1.synology_dsm.dsm_proxy:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true
    server: "proxy.example.com"
    port: 8080
    username: "proxyuser"
    password: "proxypass"

- name: Disable proxy
  stevefulme1.synology_dsm.dsm_proxy:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: false
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
      description: Proxy server address.
      type: str
      returned: always
    port:
      description: Proxy server port.
      type: int
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        enabled=dict(type='bool', required=True),
        server=dict(type='str'),
        port=dict(type='int', default=3128),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('enabled', True, ['server']),
        ],
    )

    desired_enabled = module.params['enabled']

    client = DSMClient(module)
    changed = False

    try:
        client.login()
        current = client.request('SYNO.Core.Network.Proxy', 'get', version=1)

        current_enabled = current.get('enabled', False)
        current_server = current.get('server', '')
        current_port = current.get('port', 3128)

        if desired_enabled:
            if (current_enabled != desired_enabled
                    or current_server != module.params.get('server', '')
                    or current_port != module.params['port']):
                changed = True
        else:
            if current_enabled:
                changed = True

        if changed and not module.check_mode:
            params = {'enabled': str(desired_enabled).lower()}
            if desired_enabled:
                params['server'] = module.params['server']
                params['port'] = str(module.params['port'])
                if module.params.get('username'):
                    params['username'] = module.params['username']
                if module.params.get('password'):
                    params['password'] = module.params['password']
            client.request('SYNO.Core.Network.Proxy', 'set', version=1,
                           extra_params=params)

    except DSMError as e:
        module.fail_json(msg='Failed to configure proxy: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, proxy=dict(
        enabled=desired_enabled,
        server=module.params.get('server', ''),
        port=module.params['port'],
    ))


if __name__ == '__main__':
    main()
