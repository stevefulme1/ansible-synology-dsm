#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_snapshot_info
short_description: List snapshots on Synology DSM
description:
  - Retrieves a list of Btrfs snapshots from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  share:
    description:
      - Limit results to snapshots of a specific shared folder.
    type: str
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all snapshots
  stevefulme1.synology_dsm.dsm_snapshot_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: List snapshots for a specific share
  stevefulme1.synology_dsm.dsm_snapshot_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    share: "projects"
  register: result
'''

RETURN = r'''
snapshots:
  description: List of snapshots on the DSM device.
  returned: always
  type: list
  elements: dict
  sample:
    - name: "before-upgrade"
      share: "projects"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        share=dict(type='str'),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    share = module.params.get('share')
    client = DSMClient(module)

    try:
        client.login()
        params = {}
        if share:
            params['share_name'] = share
        data = client.request(
            'SYNO.Core.Share.Snapshot', 'list', version=1,
            extra_params=params or None,
        )
    except DSMError as e:
        module.fail_json(msg='Failed to list snapshots: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, snapshots=data.get('snapshots', []))


if __name__ == '__main__':
    main()
