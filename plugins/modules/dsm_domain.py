#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_domain
short_description: Manage Active Directory domain membership on Synology DSM
description:
  - Join or leave an Active Directory domain on a Synology DSM device.
  - Enables AD user authentication when joined.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  domain:
    description:
      - The Active Directory domain name.
    type: str
  admin_user:
    description:
      - Domain administrator username for joining.
    type: str
  admin_password:
    description:
      - Domain administrator password for joining.
    type: str
  ou:
    description:
      - Organizational Unit to place the computer account in.
    type: str
  state:
    description:
      - Whether the DSM should be joined to or removed from the domain.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Join an Active Directory domain
  stevefulme1.synology_dsm.dsm_domain:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    domain: "corp.example.com"
    admin_user: "Administrator"
    admin_password: "ad_secret"
    state: present

- name: Leave the Active Directory domain
  stevefulme1.synology_dsm.dsm_domain:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    state: absent
'''

RETURN = r'''
domain:
  description: Details about the domain configuration.
  returned: always
  type: dict
  contains:
    domain_name:
      description: The Active Directory domain name.
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


def get_domain_status(client):
    """Get current Active Directory domain status."""
    try:
        data = client.request('SYNO.Core.Directory.Domain', 'get', version=1)
        return data
    except DSMError:
        return {}


def main():
    argument_spec = dict(
        domain=dict(type='str'),
        admin_user=dict(type='str'),
        admin_password=dict(type='str', no_log=True),
        ou=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['domain', 'admin_user', 'admin_password']),
        ],
    )

    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(state=state)

    try:
        client.login()
        current = get_domain_status(client)
        is_joined = current.get('enable', False)

        if state == 'present':
            if not is_joined:
                changed = True
                if not module.check_mode:
                    params = {
                        'domain_name': module.params['domain'],
                        'admin_name': module.params['admin_user'],
                        'admin_passwd': module.params['admin_password'],
                    }
                    if module.params.get('ou'):
                        params['ou'] = module.params['ou']
                    client.request(
                        'SYNO.Core.Directory.Domain', 'set', version=1,
                        extra_params=params,
                    )
                result['domain_name'] = module.params['domain']
        elif state == 'absent':
            if is_joined:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Directory.Domain', 'leave', version=1,
                    )
    except DSMError as e:
        module.fail_json(msg='Domain operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, domain=result)


if __name__ == '__main__':
    main()
