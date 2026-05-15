#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_file_station_delete
short_description: Delete files or folders on Synology DSM
description:
  - Deletes files or folders on a Synology DSM device using the File Station API.
  - Supports recursive deletion of non-empty directories.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  path:
    description:
      - The full path of the file or folder to delete.
    type: str
    required: true
  recursive:
    description:
      - Whether to recursively delete non-empty folders.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Delete a file
  stevefulme1.synology_dsm.dsm_file_station_delete:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    path: "/volume1/shared/old_file.txt"

- name: Delete a folder recursively
  stevefulme1.synology_dsm.dsm_file_station_delete:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    path: "/volume1/shared/old_folder"
    recursive: true
'''

RETURN = r'''
path:
  description: The path that was deleted.
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        path=dict(type='str', required=True),
        recursive=dict(type='bool', default=False),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    path = module.params['path']

    client = DSMClient(module)
    changed = False

    try:
        client.login()

        # Check if path exists
        try:
            client.request('SYNO.FileStation.List', 'getinfo', version=2,
                           extra_params={'path': path})
            exists = True
        except DSMError:
            exists = False

        if exists:
            changed = True
            if not module.check_mode:
                params = {
                    'path': path,
                    'recursive': str(module.params['recursive']).lower(),
                }
                client.request('SYNO.FileStation.Delete', 'delete', version=2,
                               extra_params=params)

    except DSMError as e:
        module.fail_json(msg='Failed to delete {0}: {1}'.format(path, str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, path=path)


if __name__ == '__main__':
    main()
