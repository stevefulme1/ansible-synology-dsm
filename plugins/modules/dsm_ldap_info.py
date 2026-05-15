#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_ldap_info
short_description: Get LDAP join status on Synology DSM
description:
  - Retrieves LDAP directory service join status from a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get LDAP status
  stevefulme1.synology_dsm.dsm_ldap_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display LDAP info
  ansible.builtin.debug:
    var: result.ldap_info
'''

RETURN = r'''
ldap_info:
  description: LDAP configuration and join status.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether LDAP client is enabled.
      type: bool
      returned: always
    server:
      description: LDAP server address.
      type: str
      returned: always
    base_dn:
      description: LDAP base DN.
      type: str
      returned: always
    status:
      description: Join status.
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
        data = client.request('SYNO.Core.Directory.LDAP', 'get', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to get LDAP info: {0}'.format(str(e)))
    finally:
        client.logout()

    info = dict(
        enabled=data.get('enable', False),
        server=data.get('server', ''),
        base_dn=data.get('base_dn', ''),
        status=data.get('status', 'unknown'),
    )

    module.exit_json(changed=False, ldap_info=info)


if __name__ == '__main__':
    main()
