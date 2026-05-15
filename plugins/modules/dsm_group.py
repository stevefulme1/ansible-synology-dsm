#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_group
short_description: Manage Synology DSM groups
description:
  - Create, update, or delete local groups on a Synology DSM device.
  - Supports managing group membership.
version_added: "0.1.0"
author:
  - Steve Fulmer
options:
  name:
    description:
      - The group name to manage.
    type: str
    required: true
  state:
    description:
      - Whether the group should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
  description:
    description:
      - Description for the group.
    type: str
  members:
    description:
      - List of usernames that should be members of this group.
      - When specified, the group membership will be set to exactly this list.
    type: list
    elements: str
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a DSM group
  stevefulme1.synology_dsm.dsm_group:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "developers"
    description: "Development team"
    members:
      - johndoe
      - janedoe
    state: present

- name: Remove a DSM group
  stevefulme1.synology_dsm.dsm_group:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "developers"
    state: absent
'''

RETURN = r'''
group:
  description: Details about the group that was managed.
  returned: always
  type: dict
  contains:
    name:
      description: The group name.
      type: str
      returned: always
      sample: "developers"
    state:
      description: The resulting state of the group.
      type: str
      returned: always
      sample: "present"
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import DSMClient, DSMError, dsm_argument_spec


def get_group(client, name):
    """Check if a group exists by listing all groups and searching for the name."""
    try:
        data = client.request('SYNO.Core.Group', 'list', version=1, extra_params={
            'offset': '0',
            'limit': '-1',
        })
    except DSMError:
        return None

    for group in data.get('groups', []):
        if group.get('name') == name:
            return group
    return None


def get_group_members(client, name):
    """Get current members of a group."""
    try:
        data = client.request('SYNO.Core.Group.Member', 'list', version=1, extra_params={
            'group': name,
            'offset': '0',
            'limit': '-1',
        })
    except DSMError:
        return []

    return [m.get('name') for m in data.get('members', [])]


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        description=dict(type='str'),
        members=dict(type='list', elements='str'),
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
        existing_group = get_group(client, name)
    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to query groups: {0}'.format(str(e)))

    changed = False
    result = dict(name=name, state=state)

    try:
        if state == 'present':
            if existing_group is None:
                changed = True
                if not module.check_mode:
                    group_info = dict(name=name)
                    if module.params.get('description') is not None:
                        group_info['description'] = module.params['description']
                    client.request('SYNO.Core.Group', 'create', version=1, extra_params={
                        'name': json.dumps(group_info),
                    })
                    # Set members after creation if specified
                    if module.params.get('members') is not None:
                        client.request('SYNO.Core.Group.Member', 'set', version=1, extra_params={
                            'group': name,
                            'members': json.dumps(module.params['members']),
                        })
            else:
                # Check for updates
                if module.params.get('description') is not None:
                    if existing_group.get('description', '') != module.params['description']:
                        changed = True
                        if not module.check_mode:
                            client.request('SYNO.Core.Group', 'set', version=1, extra_params={
                                'name': name,
                                'description': module.params['description'],
                            })

                if module.params.get('members') is not None:
                    current_members = sorted(get_group_members(client, name))
                    desired_members = sorted(module.params['members'])
                    if current_members != desired_members:
                        changed = True
                        if not module.check_mode:
                            client.request('SYNO.Core.Group.Member', 'set', version=1, extra_params={
                                'group': name,
                                'members': json.dumps(module.params['members']),
                            })

        elif state == 'absent':
            if existing_group is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Core.Group', 'delete', version=1, extra_params={
                        'name': json.dumps([name]),
                    })

    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to manage group {0}: {1}'.format(name, str(e)))

    client.logout()
    module.exit_json(changed=changed, group=result)


if __name__ == '__main__':
    main()
