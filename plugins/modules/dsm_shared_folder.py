#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_shared_folder
short_description: Manage Synology DSM shared folders
description:
  - Create, update, or delete shared folders on a Synology DSM device.
  - Supports setting volume path, description, recycle bin, and encryption options.
version_added: "0.1.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The shared folder name to manage.
    type: str
    required: true
  state:
    description:
      - Whether the shared folder should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
  vol_path:
    description:
      - The volume path where the shared folder is located.
      - Required when creating a new shared folder.
    type: str
    default: /volume1
  desc:
    description:
      - Description for the shared folder.
    type: str
  recycle_bin_enabled:
    description:
      - Whether the recycle bin is enabled for this shared folder.
    type: bool
    default: true
  encryption:
    description:
      - Whether folder encryption is enabled.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a shared folder
  stevefulme1.synology_dsm.dsm_shared_folder:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "projects"
    vol_path: "/volume1"
    desc: "Project files"
    recycle_bin_enabled: true
    state: present

- name: Remove a shared folder
  stevefulme1.synology_dsm.dsm_shared_folder:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "projects"
    state: absent
'''

RETURN = r'''
shared_folder:
  description: Details about the shared folder that was managed.
  returned: always
  type: dict
  contains:
    name:
      description: The shared folder name.
      type: str
      returned: always
      sample: "projects"
    state:
      description: The resulting state of the shared folder.
      type: str
      returned: always
      sample: "present"
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import DSMClient, DSMError, dsm_argument_spec


def get_shared_folder(client, name):
    """Check if a shared folder exists by listing all and searching for the name."""
    try:
        data = client.request('SYNO.Core.Share', 'list', version=1, extra_params={
            'offset': '0',
            'limit': '-1',
            'additional': json.dumps(['vol_path', 'desc', 'enable_recycle_bin', 'encryption']),
        })
    except DSMError:
        return None

    for share in data.get('shares', []):
        if share.get('name') == name:
            return share
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        vol_path=dict(type='str', default='/volume1'),
        desc=dict(type='str'),
        recycle_bin_enabled=dict(type='bool', default=True),
        encryption=dict(type='bool', default=False),
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
        existing_folder = get_shared_folder(client, name)
    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to query shared folders: {0}'.format(str(e)))

    changed = False
    result = dict(name=name, state=state)

    try:
        if state == 'present':
            if existing_folder is None:
                changed = True
                if not module.check_mode:
                    folder_info = dict(
                        name=name,
                        vol_path=module.params['vol_path'],
                        desc=module.params.get('desc') or '',
                        enable_recycle_bin=module.params['recycle_bin_enabled'],
                        encryption=module.params['encryption'],
                    )
                    client.request('SYNO.Core.Share', 'create', version=1, extra_params={
                        'name': json.dumps(folder_info),
                    })
            else:
                # Check for updates
                update_params = {}
                if module.params.get('desc') is not None:
                    if existing_folder.get('additional', {}).get('desc', '') != module.params['desc']:
                        update_params['desc'] = module.params['desc']
                if existing_folder.get('additional', {}).get('enable_recycle_bin') != module.params['recycle_bin_enabled']:
                    update_params['enable_recycle_bin'] = module.params['recycle_bin_enabled']

                if update_params:
                    changed = True
                    if not module.check_mode:
                        update_params['name'] = name
                        client.request('SYNO.Core.Share', 'set', version=1, extra_params={
                            'name': json.dumps(update_params),
                        })

        elif state == 'absent':
            if existing_folder is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Core.Share', 'delete', version=1, extra_params={
                        'name': json.dumps([name]),
                    })

    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to manage shared folder {0}: {1}'.format(name, str(e)))

    client.logout()
    module.exit_json(changed=changed, shared_folder=result)


if __name__ == '__main__':
    main()
