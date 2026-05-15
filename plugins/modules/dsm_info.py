#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_info
short_description: Gather Synology DSM system information
description:
  - Retrieves system information from a Synology DSM device including model name, RAM size,
    serial number, temperature, firmware version, and system uptime.
  - This module is read-only and does not modify any settings.
version_added: "0.1.0"
author:
  - Steve Fulmer
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get DSM system information
  stevefulme1.synology_dsm.dsm_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display DSM version
  ansible.builtin.debug:
    msg: "DSM version: {{ result.dsm_info.version }}"
'''

RETURN = r'''
dsm_info:
  description: Dictionary containing DSM system information.
  returned: always
  type: dict
  contains:
    model:
      description: The NAS model name.
      type: str
      returned: always
      sample: "DS920+"
    ram:
      description: Total RAM in MB.
      type: int
      returned: always
      sample: 4096
    serial:
      description: The device serial number.
      type: str
      returned: always
      sample: "2030PDN123456"
    temperature:
      description: System temperature in Celsius.
      type: int
      returned: always
      sample: 42
    version:
      description: DSM firmware version string.
      type: str
      returned: always
      sample: "7.2.1-69057 Update 5"
    uptime:
      description: System uptime in seconds.
      type: int
      returned: always
      sample: 864000
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import DSMClient, DSMError, dsm_argument_spec


def main():
    module = AnsibleModule(
        argument_spec=dsm_argument_spec,
        supports_check_mode=True,
    )

    client = DSMClient(module)
    client.login()

    try:
        data = client.request('SYNO.Core.System', 'info', version=3)
    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to retrieve DSM info: {0}'.format(str(e)))

    info = dict(
        model=data.get('model', ''),
        ram=data.get('ram_size', 0),
        serial=data.get('serial', ''),
        temperature=data.get('sys_temp', 0),
        version=data.get('firmware_ver', ''),
        uptime=data.get('up_time', 0),
    )

    client.logout()
    module.exit_json(changed=False, dsm_info=info)


if __name__ == '__main__':
    main()
