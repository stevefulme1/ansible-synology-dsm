#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_ssh_info
short_description: Get SSH service configuration on Synology DSM
description:
  - Retrieves SSH service status and port configuration from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get SSH configuration
  stevefulme1.synology_dsm.dsm_ssh_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display SSH configuration
  ansible.builtin.debug:
    var: result.ssh
'''

RETURN = r'''
ssh:
  description: SSH service configuration.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether SSH service is enabled.
      type: bool
      returned: always
    port:
      description: SSH listening port.
      type: int
      returned: always
  sample:
    enabled: true
    port: 22
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
        data = client.request('SYNO.Core.Terminal', 'get', version=3)

        ssh = {
            'enabled': data.get('enable_ssh', False),
            'port': data.get('ssh_port', 22),
        }
    except DSMError as e:
        module.fail_json(msg='Failed to get SSH configuration: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, ssh=ssh)


if __name__ == '__main__':
    main()
