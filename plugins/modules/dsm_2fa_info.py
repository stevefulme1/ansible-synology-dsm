#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_2fa_info
short_description: Get 2-factor authentication configuration on Synology DSM
description:
  - Retrieves the 2-factor authentication enforcement policy configuration from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get 2FA configuration
  stevefulme1.synology_dsm.dsm_2fa_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display 2FA configuration
  ansible.builtin.debug:
    var: result.twofa
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
      description: User group 2FA is enforced for (admin or all).
      type: str
      returned: always
  sample:
    enabled: true
    enforce_for: "admin"
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
        data = client.request('SYNO.Core.OTP.EnforcePolicy', 'get', version=1)

        twofa = {
            'enabled': data.get('enable', False),
            'enforce_for': 'all' if data.get('enforce_all', False) else 'admin',
        }
    except DSMError as e:
        module.fail_json(msg='Failed to get 2FA configuration: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, twofa=twofa)


if __name__ == '__main__':
    main()
