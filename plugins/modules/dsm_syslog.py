#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_syslog
short_description: Configure remote syslog on Synology DSM
description:
  - Configure remote syslog forwarding on a Synology DSM device.
  - Sends system logs to a remote syslog server.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  server:
    description:
      - The remote syslog server hostname or IP address.
    type: str
    required: true
  port:
    description:
      - The remote syslog server port.
    type: int
    default: 514
  protocol:
    description:
      - The transport protocol for syslog.
    type: str
    choices: ['udp', 'tcp']
    default: udp
  format:
    description:
      - The syslog message format.
    type: str
    choices: ['rfc3164', 'rfc5424']
    default: rfc3164
  enabled:
    description:
      - Whether remote syslog forwarding is enabled.
    type: bool
    default: true
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Configure remote syslog forwarding
  stevefulme1.synology_dsm.dsm_syslog:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    server: "syslog.example.com"
    port: 514
    protocol: udp
    enabled: true

- name: Disable remote syslog
  stevefulme1.synology_dsm.dsm_syslog:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    server: "syslog.example.com"
    enabled: false
'''

RETURN = r'''
syslog:
  description: Details about the syslog configuration.
  returned: always
  type: dict
  contains:
    server:
      description: The syslog server.
      type: str
      returned: always
    enabled:
      description: Whether remote syslog is enabled.
      type: bool
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def get_syslog_config(client):
    """Get current syslog configuration."""
    try:
        data = client.request('SYNO.Core.SyslogClient', 'get', version=1)
        return data
    except DSMError:
        return {}


def main():
    argument_spec = dict(
        server=dict(type='str', required=True),
        port=dict(type='int', default=514),
        protocol=dict(type='str', default='udp', choices=['udp', 'tcp']),
        format=dict(type='str', default='rfc3164', choices=['rfc3164', 'rfc5424']),
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
        current = get_syslog_config(client)

        needs_update = (
            current.get('server') != server
            or current.get('port') != module.params['port']
            or current.get('enabled', False) != enabled
        )

        if needs_update:
            changed = True
            if not module.check_mode:
                client.request(
                    'SYNO.Core.SyslogClient', 'set', version=1,
                    extra_params={
                        'server': server,
                        'port': str(module.params['port']),
                        'protocol': module.params['protocol'],
                        'format': module.params['format'],
                        'enabled': str(enabled).lower(),
                    },
                )
    except DSMError as e:
        module.fail_json(msg='Syslog configuration failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, syslog=result)


if __name__ == '__main__':
    main()
