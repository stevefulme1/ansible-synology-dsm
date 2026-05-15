#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_ldap
short_description: Manage LDAP directory integration on Synology DSM
description:
  - Join or leave an LDAP directory on a Synology DSM device.
  - Configures the DSM to authenticate users against an LDAP server.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  server:
    description:
      - The LDAP server hostname or IP address.
    type: str
  base_dn:
    description:
      - The LDAP base distinguished name.
    type: str
  bind_dn:
    description:
      - The bind distinguished name for LDAP authentication.
    type: str
  bind_password:
    description:
      - The password for the bind DN.
    type: str
  state:
    description:
      - Whether LDAP integration should be joined or left.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Join an LDAP directory
  stevefulme1.synology_dsm.dsm_ldap:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    server: "ldap.example.com"
    base_dn: "dc=example,dc=com"
    bind_dn: "cn=admin,dc=example,dc=com"
    bind_password: "ldap_secret"
    state: present

- name: Leave the LDAP directory
  stevefulme1.synology_dsm.dsm_ldap:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    state: absent
'''

RETURN = r'''
ldap:
  description: Details about the LDAP configuration.
  returned: always
  type: dict
  contains:
    server:
      description: The LDAP server.
      type: str
      returned: when joined
    state:
      description: The resulting state.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def get_ldap_status(client):
    """Get current LDAP configuration status."""
    try:
        data = client.request('SYNO.Core.Directory.LDAP', 'get', version=1)
        return data
    except DSMError:
        return {}


def main():
    argument_spec = dict(
        server=dict(type='str'),
        base_dn=dict(type='str'),
        bind_dn=dict(type='str'),
        bind_password=dict(type='str', no_log=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['server', 'base_dn', 'bind_dn', 'bind_password']),
        ],
    )

    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(state=state)

    try:
        client.login()
        current = get_ldap_status(client)
        is_joined = current.get('enable', False)

        if state == 'present':
            if not is_joined:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Directory.LDAP', 'set', version=1,
                        extra_params={
                            'enable': 'true',
                            'server': module.params['server'],
                            'base_dn': module.params['base_dn'],
                            'bind_dn': module.params['bind_dn'],
                            'bind_passwd': module.params['bind_password'],
                        },
                    )
                result['server'] = module.params['server']
        elif state == 'absent':
            if is_joined:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Directory.LDAP', 'set', version=1,
                        extra_params={'enable': 'false'},
                    )
    except DSMError as e:
        module.fail_json(msg='LDAP operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, ldap=result)


if __name__ == '__main__':
    main()
