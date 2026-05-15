#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_nfs_share
short_description: Manage NFS shares on Synology DSM
description:
  - Create, update, or delete NFS share rules on a Synology DSM device.
  - Configure host-level access privileges for shared folders via NFS.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The shared folder name to configure NFS access for.
    type: str
    required: true
  path:
    description:
      - The volume path of the shared folder (e.g. /volume1/data).
    type: str
  privilege:
    description:
      - Dictionary mapping host patterns to NFS permissions.
      - Keys are host/CIDR patterns, values are rw, ro, or no_access.
    type: dict
  nfs_enabled:
    description:
      - Whether NFS access is enabled for this share.
    type: bool
    default: true
  state:
    description:
      - Whether the NFS share rule should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Enable NFS access for a shared folder
  stevefulme1.synology_dsm.dsm_nfs_share:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "data"
    privilege:
      "192.168.1.0/24": rw
      "10.0.0.0/8": ro
    state: present

- name: Disable NFS for a share
  stevefulme1.synology_dsm.dsm_nfs_share:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "data"
    state: absent
'''

RETURN = r'''
nfs_share:
  description: Details about the managed NFS share.
  returned: always
  type: dict
  contains:
    name:
      description: The shared folder name.
      type: str
      returned: always
    state:
      description: The resulting state.
      type: str
      returned: always
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def get_nfs_rules(client, name):
    """Get NFS rules for a shared folder."""
    try:
        data = client.request(
            'SYNO.Core.Share', 'get', version=1,
            extra_params={'name': name, 'additional': '["nfs_privilege"]'},
        )
        shares = data.get('shares', [])
        if shares:
            return shares[0].get('additional', {}).get('nfs_privilege', [])
    except DSMError:
        pass
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        path=dict(type='str'),
        privilege=dict(type='dict'),
        nfs_enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        existing_rules = get_nfs_rules(client, name)

        if state == 'present':
            privilege = module.params.get('privilege') or {}
            nfs_rules = []
            for host, perm in privilege.items():
                nfs_rules.append({
                    'host': host,
                    'privilege': perm,
                })
            changed = True
            if not module.check_mode:
                client.request(
                    'SYNO.Core.Share', 'set', version=1,
                    extra_params={
                        'name': name,
                        'nfs_privilege': json.dumps(nfs_rules),
                    },
                )
        elif state == 'absent':
            if existing_rules:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Share', 'set', version=1,
                        extra_params={
                            'name': name,
                            'nfs_privilege': json.dumps([]),
                        },
                    )
    except DSMError as e:
        module.fail_json(msg='NFS share operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, nfs_share=result)


if __name__ == '__main__':
    main()
