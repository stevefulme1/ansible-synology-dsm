#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_vmm_info
short_description: List VMM guests on Synology DSM
description:
  - Retrieves a list of Virtual Machine Manager guests from a Synology DSM device.
  - Requires the Virtual Machine Manager package installed.
  - This module is read-only and does not modify any settings.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all VMM guests
  stevefulme1.synology_dsm.dsm_vmm_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display VMM guests
  ansible.builtin.debug:
    var: result.guests
'''

RETURN = r'''
guests:
  description: List of VMM guests on the DSM device.
  returned: always
  type: list
  elements: dict
  sample:
    - name: "ubuntu-server"
      status: "running"
      vcpu: 2
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
        data = client.request('SYNO.Virtualization.Guest', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list VMM guests: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, guests=data.get('guests', []))


if __name__ == '__main__':
    main()
