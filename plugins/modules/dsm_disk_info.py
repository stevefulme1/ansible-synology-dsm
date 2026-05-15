#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_disk_info
short_description: List disks on Synology DSM
description:
  - Retrieves a list of physical disks from a Synology DSM device.
  - Includes disk model, serial number, temperature, and health status.
  - This module is read-only and does not modify any settings.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all disks
  stevefulme1.synology_dsm.dsm_disk_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display disk information
  ansible.builtin.debug:
    var: result.disks
'''

RETURN = r'''
disks:
  description: List of physical disks on the DSM device.
  returned: always
  type: list
  elements: dict
  sample:
    - id: "sata1"
      model: "WDC WD40EFRX-68N32N0"
      serial: "WD-WCC7K0ABC123"
      temp: 35
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
        data = client.request('SYNO.Core.Storage.Disk', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list disks: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, disks=data.get('disks', []))


if __name__ == '__main__':
    main()
