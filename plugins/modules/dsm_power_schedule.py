#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_power_schedule
short_description: Configure power schedule on Synology DSM
description:
  - Configure power on/off schedules on a Synology DSM device.
  - Allows scheduling automatic shutdown and startup times.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  schedules:
    description:
      - List of schedule entries with day, time, and action.
    type: list
    elements: dict
    required: true
    suboptions:
      day:
        description:
          - Day of the week.
        type: str
        required: true
        choices: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
      time:
        description:
          - Time in HH:MM format.
        type: str
        required: true
      action:
        description:
          - Power action to perform.
        type: str
        required: true
        choices: ['shutdown', 'startup']
  enabled:
    description:
      - Whether the power schedule is enabled.
    type: bool
    default: true
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Set power schedule
  stevefulme1.synology_dsm.dsm_power_schedule:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true
    schedules:
      - day: mon
        time: "23:00"
        action: shutdown
      - day: tue
        time: "07:00"
        action: startup
'''

RETURN = r'''
power_schedule:
  description: Power schedule configuration.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether the schedule is enabled.
      type: bool
      returned: always
    schedules:
      description: List of schedule entries.
      type: list
      returned: always
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    schedule_spec = dict(
        day=dict(type='str', required=True,
                 choices=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']),
        time=dict(type='str', required=True),
        action=dict(type='str', required=True, choices=['shutdown', 'startup']),
    )

    argument_spec = dict(
        schedules=dict(type='list', elements='dict', required=True, options=schedule_spec),
        enabled=dict(type='bool', default=True),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    desired_enabled = module.params['enabled']
    desired_schedules = module.params['schedules']

    client = DSMClient(module)
    changed = False

    try:
        client.login()
        current = client.request('SYNO.Core.Hardware.PowerSchedule', 'get', version=1)

        current_enabled = current.get('enabled', False)
        current_schedules = current.get('schedules', [])

        if current_enabled != desired_enabled or current_schedules != desired_schedules:
            changed = True
            if not module.check_mode:
                client.request('SYNO.Core.Hardware.PowerSchedule', 'set', version=1,
                               extra_params={
                                   'enabled': str(desired_enabled).lower(),
                                   'schedules': json.dumps(desired_schedules),
                               })

    except DSMError as e:
        module.fail_json(msg='Failed to configure power schedule: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, power_schedule=dict(
        enabled=desired_enabled,
        schedules=desired_schedules,
    ))


if __name__ == '__main__':
    main()
