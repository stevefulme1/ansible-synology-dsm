#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_update
short_description: Manage system updates on Synology DSM
description:
  - Check for available DSM updates or apply pending updates.
  - Configure automatic update settings.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  state:
    description:
      - The update action to perform.
      - C(check) queries for available updates without applying them.
      - C(apply) downloads and installs any pending update.
    type: str
    choices: ['check', 'apply']
    default: check
  auto_update:
    description:
      - Whether automatic updates are enabled.
    type: bool
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Check for DSM updates
  stevefulme1.synology_dsm.dsm_update:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    state: check
  register: result

- name: Apply pending DSM update
  stevefulme1.synology_dsm.dsm_update:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    state: apply

- name: Enable automatic updates
  stevefulme1.synology_dsm.dsm_update:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    auto_update: true
'''

RETURN = r'''
update:
  description: Details about the update status.
  returned: always
  type: dict
  contains:
    available:
      description: Whether an update is available.
      type: bool
      returned: always
    version:
      description: Available update version.
      type: str
      returned: when available
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        state=dict(type='str', default='check', choices=['check', 'apply']),
        auto_update=dict(type='bool'),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params['state']
    auto_update = module.params.get('auto_update')

    client = DSMClient(module)
    changed = False
    result = dict(available=False)

    try:
        client.login()

        # Handle auto_update setting
        if auto_update is not None:
            current = client.request('SYNO.Core.Upgrade', 'get', version=1)
            if current.get('auto_update', False) != auto_update:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Upgrade', 'set', version=1,
                        extra_params={
                            'auto_update': str(auto_update).lower(),
                        },
                    )

        if state == 'check':
            data = client.request(
                'SYNO.Core.Upgrade', 'check', version=1,
            )
            result['available'] = data.get('available', False)
            if data.get('version'):
                result['version'] = data['version']

        elif state == 'apply':
            if module.check_mode:
                changed = True
            else:
                data = client.request(
                    'SYNO.Core.Upgrade', 'check', version=1,
                )
                if data.get('available', False):
                    changed = True
                    client.request(
                        'SYNO.Core.Upgrade', 'start', version=1,
                    )
                    result['available'] = True
                    if data.get('version'):
                        result['version'] = data['version']

    except DSMError as e:
        module.fail_json(msg='Update operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, update=result)


if __name__ == '__main__':
    main()
