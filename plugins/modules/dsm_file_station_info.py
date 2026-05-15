#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_file_station_info
short_description: Get Synology File Station information
description:
  - Retrieves File Station information including supported protocols, hostname, and manager status.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get File Station info
  stevefulme1.synology_dsm.dsm_file_station_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display hostname
  ansible.builtin.debug:
    msg: "Hostname: {{ result.file_station_info.hostname }}"
'''

RETURN = r'''
file_station_info:
  description: Dictionary containing File Station information.
  returned: always
  type: dict
  contains:
    hostname:
      description: The NAS hostname.
      type: str
      returned: always
    support_sharing:
      description: Whether file sharing is supported.
      type: bool
      returned: always
    is_manager:
      description: Whether the current user is a manager.
      type: bool
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    module = AnsibleModule(
        argument_spec=dsm_argument_spec,
        supports_check_mode=True,
    )

    client = DSMClient(module)

    try:
        client.login()
        data = client.request('SYNO.FileStation.Info', 'get', version=2)
    except DSMError as e:
        module.fail_json(msg='Failed to retrieve File Station info: {0}'.format(str(e)))
    finally:
        client.logout()

    info = dict(
        hostname=data.get('hostname', ''),
        support_sharing=data.get('support_sharing', False),
        is_manager=data.get('is_manager', False),
    )

    module.exit_json(changed=False, file_station_info=info)


if __name__ == '__main__':
    main()
