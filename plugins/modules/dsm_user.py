#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_user
short_description: Manage Synology DSM users
description:
  - Create, update, or delete local users on a Synology DSM device.
  - Supports setting password, description, email, and account status.
version_added: "0.1.0"
author:
  - Steve Fulmer
options:
  name:
    description:
      - The username to manage.
    type: str
    required: true
  state:
    description:
      - Whether the user should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
  password:
    description:
      - Password for the user. Required when creating a new user.
    type: str
    no_log: true
  description:
    description:
      - Description for the user account.
    type: str
  email:
    description:
      - Email address for the user.
    type: str
  cannot_change_password:
    description:
      - Whether the user is prevented from changing their own password.
    type: bool
    default: false
  is_disabled:
    description:
      - Whether the user account is disabled.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a DSM user
  stevefulme1.synology_dsm.dsm_user:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "johndoe"
    password: "user_password"
    description: "John Doe user account"
    email: "john@example.com"
    state: present

- name: Disable a DSM user
  stevefulme1.synology_dsm.dsm_user:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "johndoe"
    is_disabled: true
    state: present

- name: Remove a DSM user
  stevefulme1.synology_dsm.dsm_user:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "johndoe"
    state: absent
'''

RETURN = r'''
user:
  description: Details about the user that was managed.
  returned: always
  type: dict
  contains:
    name:
      description: The username.
      type: str
      returned: always
      sample: "johndoe"
    state:
      description: The resulting state of the user.
      type: str
      returned: always
      sample: "present"
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import DSMClient, DSMError, dsm_argument_spec


def get_user(client, name):
    """Check if a user exists by listing all users and searching for the name."""
    try:
        data = client.request('SYNO.Core.User', 'list', version=1, extra_params={
            'offset': '0',
            'limit': '-1',
        })
    except DSMError:
        return None

    for user in data.get('users', []):
        if user.get('name') == name:
            return user
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        password=dict(type='str', no_log=True),
        description=dict(type='str'),
        email=dict(type='str'),
        cannot_change_password=dict(type='bool', default=False),
        is_disabled=dict(type='bool', default=False),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    client.login()

    try:
        existing_user = get_user(client, name)
    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to query users: {0}'.format(str(e)))

    changed = False
    result = dict(name=name, state=state)

    try:
        if state == 'present':
            if existing_user is None:
                # Create user
                if module.params['password'] is None:
                    client.logout()
                    module.fail_json(msg='password is required when creating a new user')
                changed = True
                if not module.check_mode:
                    user_info = dict(
                        name=name,
                        password=module.params['password'],
                        description=module.params.get('description') or '',
                        email=module.params.get('email') or '',
                        cannot_chg_passwd=module.params['cannot_change_password'],
                        expired='normal' if not module.params['is_disabled'] else 'disabled',
                    )
                    client.request('SYNO.Core.User', 'create', version=1, extra_params={
                        'name': json.dumps(user_info),
                    })
            else:
                # Update user if needed
                update_params = {}
                if module.params.get('description') is not None:
                    if existing_user.get('description', '') != module.params['description']:
                        update_params['description'] = module.params['description']
                if module.params.get('email') is not None:
                    if existing_user.get('email', '') != module.params['email']:
                        update_params['email'] = module.params['email']
                if module.params['cannot_change_password'] != existing_user.get('cannot_chg_passwd', False):
                    update_params['cannot_chg_passwd'] = module.params['cannot_change_password']

                desired_expired = 'disabled' if module.params['is_disabled'] else 'normal'
                if existing_user.get('expired', 'normal') != desired_expired:
                    update_params['expired'] = desired_expired

                if module.params.get('password') is not None:
                    update_params['password'] = module.params['password']
                    changed = True

                if update_params:
                    changed = True
                    if not module.check_mode:
                        update_params['name'] = name
                        client.request('SYNO.Core.User', 'set', version=1, extra_params={
                            'name': json.dumps(update_params),
                        })

        elif state == 'absent':
            if existing_user is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Core.User', 'delete', version=1, extra_params={
                        'name': json.dumps([name]),
                    })

    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to manage user {0}: {1}'.format(name, str(e)))

    client.logout()
    module.exit_json(changed=changed, user=result)


if __name__ == '__main__':
    main()
