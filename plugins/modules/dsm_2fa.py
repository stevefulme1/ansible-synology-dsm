#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_2fa
short_description: Configure 2-factor authentication on Synology DSM
description:
  - Configure 2-factor authentication enforcement policy on a Synology DSM device.
  - Can enforce 2FA for administrators only or all users.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  enabled:
    description:
      - Whether 2FA enforcement is enabled.
    type: bool
    required: true
  enforce_for:
    description:
      - Which user group to enforce 2FA for.
    type: str
    choices: ['admin', 'all']
    default: admin
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Enforce 2FA for administrators
  stevefulme1.synology_dsm.dsm_2fa:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true
    enforce_for: admin

- name: Enforce 2FA for all users
  stevefulme1.synology_dsm.dsm_2fa:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true
    enforce_for: all

- name: Disable 2FA enforcement
  stevefulme1.synology_dsm.dsm_2fa:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: false
'''

RETURN = r'''
twofa:
  description: 2FA enforcement configuration.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether 2FA enforcement is enabled.
      type: bool
      returned: always
    enforce_for:
      description: User group 2FA is enforced for.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        enabled=dict(type='bool', required=True),
        enforce_for=dict(type='str', default='admin', choices=['admin', 'all']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    desired_enabled = module.params['enabled']
    desired_enforce_for = module.params['enforce_for']

    client = DSMClient(module)
    changed = False

    try:
        client.login()
        current = client.request('SYNO.Core.OTP.EnforcePolicy', 'get', version=1)

        current_enabled = current.get('enable', False)
        current_enforce = 'all' if current.get('enforce_all', False) else 'admin'

        if current_enabled != desired_enabled or current_enforce != desired_enforce_for:
            changed = True
            if not module.check_mode:
                params = {
                    'enable': str(desired_enabled).lower(),
                    'enforce_all': str(desired_enforce_for == 'all').lower(),
                }
                client.request('SYNO.Core.OTP.EnforcePolicy', 'set', version=1,
                               extra_params=params)

    except DSMError as e:
        module.fail_json(msg='Failed to configure 2FA: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, twofa=dict(
        enabled=desired_enabled,
        enforce_for=desired_enforce_for,
    ))


if __name__ == '__main__':
    main()
