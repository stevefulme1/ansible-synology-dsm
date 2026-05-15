#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_file_station_list
short_description: List files and folders on Synology DSM
description:
  - Lists files and folders in a specified path on a Synology DSM device via File Station.
  - Supports filtering by pattern and file type.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  folder_path:
    description:
      - The folder path to list contents of.
    type: str
    required: true
  pattern:
    description:
      - Glob pattern to filter results.
    type: str
  filetype:
    description:
      - Filter by file type.
    type: str
    choices: ['file', 'dir', 'all']
    default: all
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List files in shared folder
  stevefulme1.synology_dsm.dsm_file_station_list:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    folder_path: "/volume1/shared"
  register: result

- name: List only text files
  stevefulme1.synology_dsm.dsm_file_station_list:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    folder_path: "/volume1/shared"
    pattern: "*.txt"
    filetype: file
'''

RETURN = r'''
files:
  description: List of files and folders found.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: File or folder name.
      type: str
      returned: always
    path:
      description: Full path.
      type: str
      returned: always
    isdir:
      description: Whether the entry is a directory.
      type: bool
      returned: always
total:
  description: Total number of items found.
  returned: always
  type: int
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        folder_path=dict(type='str', required=True),
        pattern=dict(type='str'),
        filetype=dict(type='str', default='all', choices=['file', 'dir', 'all']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    client = DSMClient(module)

    try:
        client.login()
        params = {'folder_path': module.params['folder_path']}
        if module.params.get('pattern'):
            params['pattern'] = module.params['pattern']
        if module.params['filetype'] != 'all':
            params['filetype'] = module.params['filetype']

        data = client.request('SYNO.FileStation.List', 'list', version=2,
                              extra_params=params)
    except DSMError as e:
        module.fail_json(msg='Failed to list files: {0}'.format(str(e)))
    finally:
        client.logout()

    files = []
    for item in data.get('files', []):
        files.append(dict(
            name=item.get('name', ''),
            path=item.get('path', ''),
            isdir=item.get('isdir', False),
        ))

    module.exit_json(changed=False, files=files, total=data.get('total', 0))


if __name__ == '__main__':
    main()
