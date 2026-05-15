#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_resource_monitor_info
short_description: Get resource usage on Synology DSM
description:
  - Retrieves current resource utilization from a Synology DSM device.
  - Returns CPU, memory, network, and disk usage information.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Get resource utilization
  stevefulme1.synology_dsm.dsm_resource_monitor_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display CPU usage
  ansible.builtin.debug:
    msg: "CPU usage: {{ result.utilization.cpu }}%"
'''

RETURN = r'''
utilization:
  description: Current resource utilization.
  returned: always
  type: dict
  contains:
    cpu:
      description: CPU utilization percentage.
      type: int
      returned: always
      sample: 15
    memory:
      description: Memory utilization percentage.
      type: int
      returned: always
      sample: 65
    network:
      description: Network utilization in bytes per second.
      type: dict
      returned: always
    disk:
      description: Disk utilization information.
      type: dict
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
        data = client.request('SYNO.Core.System.Utilization', 'get', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to get resource utilization: {0}'.format(str(e)))
    finally:
        client.logout()

    cpu_data = data.get('cpu', {})
    memory_data = data.get('memory', {})

    utilization = dict(
        cpu=cpu_data.get('user', 0) + cpu_data.get('system', 0),
        memory=memory_data.get('real_usage', 0),
        network=data.get('network', {}),
        disk=data.get('disk', {}),
    )

    module.exit_json(changed=False, utilization=utilization)


if __name__ == '__main__':
    main()
