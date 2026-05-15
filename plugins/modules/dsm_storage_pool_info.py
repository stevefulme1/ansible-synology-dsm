#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_storage_pool_info
short_description: List storage pools on Synology DSM
description:
  - Retrieves a list of storage pools from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all storage pools
  stevefulme1.synology_dsm.dsm_storage_pool_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display storage pools
  ansible.builtin.debug:
    var: result.storage_pools
'''

RETURN = r'''
storage_pools:
  description: List of storage pools on the DSM device.
  returned: always
  type: list
  elements: dict
  sample:
    - id: 1
      name: "pool1"
      raid_type: "shr"
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
        data = client.request('SYNO.Core.Storage.Pool', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list storage pools: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, storage_pools=data.get('pools', []))


if __name__ == '__main__':
    main()
