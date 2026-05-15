#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_ddns
short_description: Configure DDNS on Synology DSM
description:
  - Create, update, or delete Dynamic DNS records on a Synology DSM device.
  - Supports Synology and third-party DDNS providers.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  provider:
    description:
      - The DDNS service provider name.
    type: str
  hostname:
    description:
      - The DDNS hostname to register.
    type: str
  username:
    description:
      - The DDNS account username.
    type: str
  password:
    description:
      - The DDNS account password or API key.
    type: str
  state:
    description:
      - Whether the DDNS record should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Configure a DDNS record
  stevefulme1.synology_dsm.dsm_ddns:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    provider: "Synology"
    hostname: "mynas.synology.me"
    username: "myaccount"
    password: "ddns_password"
    state: present

- name: Remove a DDNS record
  stevefulme1.synology_dsm.dsm_ddns:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    hostname: "mynas.synology.me"
    state: absent
'''

RETURN = r'''
ddns:
  description: Details about the DDNS configuration.
  returned: always
  type: dict
  contains:
    hostname:
      description: The DDNS hostname.
      type: str
      returned: when configured
    state:
      description: The resulting state.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_ddns_record(client, hostname):
    """Find a DDNS record by hostname."""
    try:
        data = client.request('SYNO.Core.DDNS.Record', 'list', version=1)
        for record in data.get('records', []):
            if record.get('hostname') == hostname:
                return record
    except DSMError:
        pass
    return None


def main():
    argument_spec = dict(
        provider=dict(type='str'),
        hostname=dict(type='str'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['provider', 'hostname', 'username', 'password']),
            ('state', 'absent', ['hostname']),
        ],
    )

    hostname = module.params.get('hostname')
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(state=state)
    if hostname:
        result['hostname'] = hostname

    try:
        client.login()
        existing = find_ddns_record(client, hostname) if hostname else None

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.DDNS.Record', 'create', version=1,
                        extra_params={
                            'provider': module.params['provider'],
                            'hostname': hostname,
                            'username': module.params['username'],
                            'password': module.params['password'],
                        },
                    )
        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    record_id = existing.get('id', hostname)
                    client.request(
                        'SYNO.Core.DDNS.Record', 'delete', version=1,
                        extra_params={'id': str(record_id)},
                    )
    except DSMError as e:
        module.fail_json(msg='DDNS operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, ddns=result)


if __name__ == '__main__':
    main()
