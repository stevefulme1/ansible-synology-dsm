#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_iscsi_target
short_description: Manage iSCSI targets on Synology DSM
description:
  - Create, update, or delete iSCSI targets on a Synology DSM device.
  - Requires the iSCSI Manager package or built-in iSCSI support.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The iSCSI target name.
    type: str
    required: true
  iqn:
    description:
      - The iSCSI Qualified Name for the target.
    type: str
  auth_type:
    description:
      - Authentication method for the target.
    type: str
    choices: ['none', 'chap', 'mutual_chap']
    default: none
  chap_user:
    description:
      - CHAP username when auth_type is chap or mutual_chap.
    type: str
  chap_password:
    description:
      - CHAP password when auth_type is chap or mutual_chap.
    type: str
  state:
    description:
      - Whether the target should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create an iSCSI target
  stevefulme1.synology_dsm.dsm_iscsi_target:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "target1"
    iqn: "iqn.2000-01.com.synology:ds920.target1"
    auth_type: none
    state: present

- name: Remove an iSCSI target
  stevefulme1.synology_dsm.dsm_iscsi_target:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "target1"
    state: absent
'''

RETURN = r'''
iscsi_target:
  description: Details about the managed iSCSI target.
  returned: always
  type: dict
  contains:
    name:
      description: The target name.
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


def find_target(client, name):
    """Find an iSCSI target by name."""
    data = client.request('SYNO.Core.ISCSI.Target', 'list', version=1)
    for target in data.get('targets', []):
        if target.get('name') == name:
            return target
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        iqn=dict(type='str'),
        auth_type=dict(type='str', default='none',
                       choices=['none', 'chap', 'mutual_chap']),
        chap_user=dict(type='str'),
        chap_password=dict(type='str', no_log=True),
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
        existing = find_target(client, name)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    params = {
                        'name': name,
                        'auth_type': module.params['auth_type'],
                    }
                    if module.params.get('iqn'):
                        params['iqn'] = module.params['iqn']
                    if module.params.get('chap_user'):
                        params['chap_user'] = module.params['chap_user']
                    if module.params.get('chap_password'):
                        params['chap_password'] = module.params['chap_password']
                    client.request(
                        'SYNO.Core.ISCSI.Target', 'create', version=1,
                        extra_params=params,
                    )
        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    target_id = existing.get('target_id', existing.get('id'))
                    client.request(
                        'SYNO.Core.ISCSI.Target', 'delete', version=1,
                        extra_params={'target_id': str(target_id)},
                    )
    except DSMError as e:
        module.fail_json(msg='iSCSI target operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, iscsi_target=result)


if __name__ == '__main__':
    main()
