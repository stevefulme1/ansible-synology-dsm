#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_ssh
short_description: Configure SSH service on Synology DSM
description:
  - Enable or disable the SSH service on a Synology DSM device.
  - Allows configuring the SSH listening port.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  enabled:
    description:
      - Whether the SSH service should be enabled.
    type: bool
    required: true
  port:
    description:
      - The port number for the SSH service.
    type: int
    default: 22
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Enable SSH on default port
  stevefulme1.synology_dsm.dsm_ssh:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true

- name: Enable SSH on custom port
  stevefulme1.synology_dsm.dsm_ssh:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true
    port: 2222

- name: Disable SSH
  stevefulme1.synology_dsm.dsm_ssh:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: false
'''

RETURN = r'''
ssh:
  description: SSH service configuration.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether SSH is enabled.
      type: bool
      returned: always
    port:
      description: The SSH port number.
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
        port=dict(type='int', default=22),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    desired_enabled = module.params['enabled']
    desired_port = module.params['port']

    client = DSMClient(module)
    changed = False

    try:
        client.login()
        current = client.request('SYNO.Core.Terminal', 'get', version=3)

        current_enabled = current.get('enable_ssh', False)
        current_port = current.get('ssh_port', 22)

        if current_enabled != desired_enabled or current_port != desired_port:
            changed = True
            if not module.check_mode:
                client.request('SYNO.Core.Terminal', 'set', version=3,
                               extra_params={
                                   'enable_ssh': str(desired_enabled).lower(),
                                   'ssh_port': str(desired_port),
                               })

    except DSMError as e:
        module.fail_json(msg='Failed to configure SSH: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, ssh=dict(enabled=desired_enabled, port=desired_port))


if __name__ == '__main__':
    main()
