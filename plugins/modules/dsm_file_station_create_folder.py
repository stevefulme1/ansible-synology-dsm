#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_file_station_create_folder
short_description: Create folders on Synology DSM via File Station
description:
  - Creates one or more folders on a Synology DSM device using the File Station API.
  - Supports creating parent directories automatically with the force_parent option.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  folder_path:
    description:
      - List of parent paths where folders will be created.
    type: list
    elements: str
    required: true
  name:
    description:
      - List of folder names to create, corresponding to each folder_path entry.
    type: list
    elements: str
    required: true
  force_parent:
    description:
      - Whether to create parent directories if they do not exist.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a single folder
  stevefulme1.synology_dsm.dsm_file_station_create_folder:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    folder_path:
      - "/volume1/shared"
    name:
      - "projects"

- name: Create nested folder with parents
  stevefulme1.synology_dsm.dsm_file_station_create_folder:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    folder_path:
      - "/volume1/shared"
    name:
      - "projects/2026/q1"
    force_parent: true
'''

RETURN = r'''
folders:
  description: List of folders that were created.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: The folder name.
      type: str
      returned: always
    path:
      description: The full path of the created folder.
      type: str
      returned: always
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        folder_path=dict(type='list', elements='str', required=True),
        name=dict(type='list', elements='str', required=True),
        force_parent=dict(type='bool', default=False),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    folder_paths = module.params['folder_path']
    names = module.params['name']

    if len(folder_paths) != len(names):
        module.fail_json(msg='folder_path and name lists must have the same length.')

    client = DSMClient(module)
    changed = False
    created = []

    try:
        client.login()

        # Check which folders already exist
        for idx, (fpath, fname) in enumerate(zip(folder_paths, names)):
            full_path = '{0}/{1}'.format(fpath.rstrip('/'), fname)
            try:
                client.request('SYNO.FileStation.List', 'getinfo', version=2,
                               extra_params={'path': full_path})
                # Folder already exists
                created.append(dict(name=fname, path=full_path))
            except DSMError:
                # Folder does not exist, needs creation
                changed = True
                created.append(dict(name=fname, path=full_path))

        if changed and not module.check_mode:
            params = {
                'folder_path': json.dumps(folder_paths),
                'name': json.dumps(names),
                'force_parent': str(module.params['force_parent']).lower(),
            }
            client.request('SYNO.FileStation.CreateFolder', 'create', version=2,
                           extra_params=params)

    except DSMError as e:
        module.fail_json(msg='Failed to create folders: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, folders=created)


if __name__ == '__main__':
    main()
