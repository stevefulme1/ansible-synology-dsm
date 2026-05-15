#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_nfs_share_info
short_description: List NFS shares on Synology DSM
description:
  - Retrieves a list of shared folders with NFS privileges from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List NFS shares
  stevefulme1.synology_dsm.dsm_nfs_share_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display NFS shares
  ansible.builtin.debug:
    var: result.nfs_shares
'''

RETURN = r'''
nfs_shares:
  description: List of shared folders with NFS privileges.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Share name.
      type: str
      returned: always
    path:
      description: Share path.
      type: str
      returned: always
    nfs_enabled:
      description: Whether NFS is enabled for this share.
      type: bool
      returned: always
'''

import json

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
        data = client.request('SYNO.Core.Share', 'list', version=1, extra_params={
            'offset': '0',
            'limit': '-1',
            'additional': json.dumps(['nfs_privilege']),
        })
    except DSMError as e:
        module.fail_json(msg='Failed to list NFS shares: {0}'.format(str(e)))
    finally:
        client.logout()

    shares = []
    for share in data.get('shares', []):
        additional = share.get('additional', {})
        nfs_privs = additional.get('nfs_privilege', [])
        shares.append(dict(
            name=share.get('name', ''),
            path=share.get('path', ''),
            nfs_enabled=len(nfs_privs) > 0,
        ))

    module.exit_json(changed=False, nfs_shares=shares)


if __name__ == '__main__':
    main()
