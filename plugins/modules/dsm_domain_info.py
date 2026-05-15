#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_domain_info
short_description: Get Active Directory domain join status on Synology DSM
description:
  - Retrieves Active Directory domain join status from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get domain join status
  stevefulme1.synology_dsm.dsm_domain_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display domain info
  ansible.builtin.debug:
    var: result.domain_info
'''

RETURN = r'''
domain_info:
  description: Active Directory domain configuration and status.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether AD domain join is enabled.
      type: bool
      returned: always
    domain:
      description: Domain name.
      type: str
      returned: always
    status:
      description: Join status.
      type: str
      returned: always
    dc:
      description: Domain controller address.
      type: str
      returned: always
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
        data = client.request('SYNO.Core.Directory.Domain', 'get', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to get domain info: {0}'.format(str(e)))
    finally:
        client.logout()

    info = dict(
        enabled=data.get('enable', False),
        domain=data.get('domain', ''),
        status=data.get('status', 'unknown'),
        dc=data.get('dc_ip', ''),
    )

    module.exit_json(changed=False, domain_info=info)


if __name__ == '__main__':
    main()
