#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_ntp_info
short_description: Get NTP configuration on Synology DSM
description:
  - Retrieves NTP server and time synchronization configuration from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get NTP configuration
  stevefulme1.synology_dsm.dsm_ntp_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display NTP configuration
  ansible.builtin.debug:
    var: result.ntp
'''

RETURN = r'''
ntp:
  description: NTP configuration.
  returned: always
  type: dict
  contains:
    server:
      description: NTP server hostname or IP address.
      type: str
      returned: always
    enabled:
      description: Whether NTP time synchronization is enabled.
      type: bool
      returned: always
  sample:
    server: "pool.ntp.org"
    enabled: true
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
        data = client.request('SYNO.Core.NTPServer', 'get', version=1)

        ntp = {
            'server': data.get('server', ''),
            'enabled': data.get('enabled', True),
        }
    except DSMError as e:
        module.fail_json(msg='Failed to get NTP configuration: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, ntp=ntp)


if __name__ == '__main__':
    main()
