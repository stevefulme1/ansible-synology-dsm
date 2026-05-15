#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_notification
short_description: Configure push notifications on Synology DSM
description:
  - Configure push notification settings on a Synology DSM device.
  - Supports enabling and disabling notification services.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  enabled:
    description:
      - Whether push notifications are enabled.
    type: bool
    required: true
  service:
    description:
      - Notification delivery service.
    type: str
    choices: ['mail', 'sms', 'push']
    default: push
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Enable push notifications
  stevefulme1.synology_dsm.dsm_notification:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: true
    service: push

- name: Disable notifications
  stevefulme1.synology_dsm.dsm_notification:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    enabled: false
'''

RETURN = r'''
notification:
  description: Notification configuration.
  returned: always
  type: dict
  contains:
    enabled:
      description: Whether notifications are enabled.
      type: bool
      returned: always
    service:
      description: Notification service type.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def main():
    argument_spec = dict(
        enabled=dict(type='bool', required=True),
        service=dict(type='str', default='push', choices=['mail', 'sms', 'push']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    desired_enabled = module.params['enabled']
    desired_service = module.params['service']

    client = DSMClient(module)
    changed = False

    try:
        client.login()
        current = client.request('SYNO.Core.Notification.Push', 'get', version=1)

        current_enabled = current.get('enabled', False)
        current_service = current.get('service', 'push')

        if current_enabled != desired_enabled or current_service != desired_service:
            changed = True
            if not module.check_mode:
                client.request('SYNO.Core.Notification.Push', 'set', version=1,
                               extra_params={
                                   'enabled': str(desired_enabled).lower(),
                                   'service': desired_service,
                               })

    except DSMError as e:
        module.fail_json(msg='Failed to configure notifications: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, notification=dict(
        enabled=desired_enabled,
        service=desired_service,
    ))


if __name__ == '__main__':
    main()
