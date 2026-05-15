#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_file_station_rename
short_description: Rename files or folders on Synology DSM
description:
  - Renames a file or folder on a Synology DSM device using the File Station API.
  - The target must already exist at the specified path.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  path:
    description:
      - The full path of the file or folder to rename.
    type: str
    required: true
  name:
    description:
      - The new name for the file or folder.
    type: str
    required: true
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Rename a folder
  stevefulme1.synology_dsm.dsm_file_station_rename:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    path: "/volume1/shared/old_name"
    name: "new_name"

- name: Rename a file
  stevefulme1.synology_dsm.dsm_file_station_rename:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    path: "/volume1/shared/report.txt"
    name: "report_final.txt"
'''

RETURN = r'''
file:
  description: Details about the renamed file or folder.
  returned: always
  type: dict
  contains:
    path:
      description: The original path.
      type: str
      returned: always
    name:
      description: The new name.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        path=dict(type='str', required=True),
        name=dict(type='str', required=True),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    path = module.params['path']
    new_name = module.params['name']
    current_name = path.rstrip('/').rsplit('/', 1)[-1]

    client = DSMClient(module)
    changed = False

    try:
        client.login()

        if current_name == new_name:
            # Already has the desired name
            changed = False
        else:
            changed = True
            if not module.check_mode:
                client.request('SYNO.FileStation.Rename', 'rename', version=2,
                               extra_params={'path': path, 'name': new_name})

    except DSMError as e:
        module.fail_json(msg='Failed to rename {0}: {1}'.format(path, str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, file=dict(path=path, name=new_name))


if __name__ == '__main__':
    main()
