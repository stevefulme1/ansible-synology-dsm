#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_mail
short_description: Configure mail notification on Synology DSM
description:
  - Configure SMTP mail notification settings on a Synology DSM device.
  - Used for system event notifications and alerts.
version_added: "0.3.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  smtp_server:
    description:
      - The SMTP server hostname or IP address.
    type: str
  smtp_port:
    description:
      - The SMTP server port.
    type: int
    default: 587
  sender:
    description:
      - The sender email address for notifications.
    type: str
  username:
    description:
      - SMTP authentication username.
    type: str
  password:
    description:
      - SMTP authentication password.
    type: str
  use_tls:
    description:
      - Whether to use TLS encryption for SMTP.
    type: bool
    default: true
  state:
    description:
      - Whether mail notification should be enabled or disabled.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Configure SMTP mail notification
  stevefulme1.synology_dsm.dsm_mail:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender: "nas@example.com"
    username: "nas@example.com"
    password: "app_password"
    use_tls: true
    state: present

- name: Disable mail notification
  stevefulme1.synology_dsm.dsm_mail:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    state: absent
'''

RETURN = r'''
mail:
  description: Details about the mail notification configuration.
  returned: always
  type: dict
  contains:
    smtp_server:
      description: The SMTP server.
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


def get_mail_config(client):
    """Get current mail notification configuration."""
    try:
        data = client.request(
            'SYNO.Core.Notification.Mail', 'get', version=1,
        )
        return data
    except DSMError:
        return {}


def main():
    argument_spec = dict(
        smtp_server=dict(type='str'),
        smtp_port=dict(type='int', default=587),
        sender=dict(type='str'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        use_tls=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['smtp_server', 'sender']),
        ],
    )

    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(state=state)

    try:
        client.login()
        current = get_mail_config(client)

        if state == 'present':
            params = {
                'enable': 'true',
                'smtp_server': module.params['smtp_server'],
                'smtp_port': str(module.params['smtp_port']),
                'sender': module.params['sender'],
                'use_tls': str(module.params['use_tls']).lower(),
            }
            if module.params.get('username'):
                params['smtp_auth'] = 'true'
                params['smtp_username'] = module.params['username']
            if module.params.get('password'):
                params['smtp_password'] = module.params['password']

            needs_update = (
                current.get('smtp_server') != module.params['smtp_server']
                or current.get('sender') != module.params['sender']
                or not current.get('enable', False)
            )
            if needs_update:
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Notification.Mail', 'set', version=1,
                        extra_params=params,
                    )
            result['smtp_server'] = module.params['smtp_server']

        elif state == 'absent':
            if current.get('enable', False):
                changed = True
                if not module.check_mode:
                    client.request(
                        'SYNO.Core.Notification.Mail', 'set', version=1,
                        extra_params={'enable': 'false'},
                    )
    except DSMError as e:
        module.fail_json(msg='Mail configuration failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, mail=result)


if __name__ == '__main__':
    main()
