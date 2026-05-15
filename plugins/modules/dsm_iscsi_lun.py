#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_iscsi_lun
short_description: Manage iSCSI LUNs on Synology DSM
description:
  - Create, update, or delete iSCSI LUNs on a Synology DSM device.
  - LUNs can be mapped to iSCSI targets for block-level storage access.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The LUN name.
    type: str
    required: true
  location:
    description:
      - Volume path for the LUN (e.g. /volume1).
    type: str
  size:
    description:
      - LUN size in GB.
    type: int
  target:
    description:
      - iSCSI target name or ID to map this LUN to.
    type: str
  thin_provisioning:
    description:
      - Whether to use thin provisioning for the LUN.
    type: bool
    default: true
  state:
    description:
      - Whether the LUN should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a thin-provisioned iSCSI LUN
  stevefulme1.synology_dsm.dsm_iscsi_lun:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "lun1"
    location: "/volume1"
    size: 100
    target: "target1"
    thin_provisioning: true
    state: present

- name: Remove an iSCSI LUN
  stevefulme1.synology_dsm.dsm_iscsi_lun:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "lun1"
    state: absent
'''

RETURN = r'''
iscsi_lun:
  description: Details about the managed iSCSI LUN.
  returned: always
  type: dict
  contains:
    name:
      description: The LUN name.
      type: str
      returned: always
    state:
      description: The resulting state.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_lun(client, name):
    """Find an iSCSI LUN by name."""
    data = client.request('SYNO.Core.ISCSI.LUN', 'list', version=1)
    for lun in data.get('luns', []):
        if lun.get('name') == name:
            return lun
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        location=dict(type='str'),
        size=dict(type='int'),
        target=dict(type='str'),
        thin_provisioning=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['location', 'size']),
        ],
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        existing = find_lun(client, name)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    params = {
                        'name': name,
                        'location': module.params['location'],
                        'size': str(module.params['size']),
                        'thin_provisioning': str(module.params['thin_provisioning']).lower(),
                    }
                    if module.params.get('target'):
                        params['target'] = module.params['target']
                    client.request(
                        'SYNO.Core.ISCSI.LUN', 'create', version=1,
                        extra_params=params,
                    )
        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    lun_id = existing.get('lun_id', existing.get('id'))
                    client.request(
                        'SYNO.Core.ISCSI.LUN', 'delete', version=1,
                        extra_params={'lun_id': str(lun_id)},
                    )
    except DSMError as e:
        module.fail_json(msg='iSCSI LUN operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, iscsi_lun=result)


if __name__ == '__main__':
    main()
