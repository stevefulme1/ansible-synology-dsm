#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_service
short_description: Enable or disable Synology DSM services
description:
  - Enable or disable system services on a Synology DSM device.
  - Common services include SSH, NFS, SMB/CIFS, FTP, and others.
version_added: "0.1.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The service name to manage (e.g. "ssh", "nfs", "smb", "ftp", "rsync").
    type: str
    required: true
  enabled:
    description:
      - Whether the service should be enabled or disabled.
    type: bool
    required: true
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Enable SSH service
  stevefulme1.synology_dsm.dsm_service:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "ssh"
    enabled: true

- name: Disable NFS service
  stevefulme1.synology_dsm.dsm_service:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "nfs"
    enabled: false
'''

RETURN = r'''
service:
  description: Details about the service that was managed.
  returned: always
  type: dict
  contains:
    name:
      description: The service name.
      type: str
      returned: always
      sample: "ssh"
    enabled:
      description: Whether the service is enabled.
      type: bool
      returned: always
      sample: true
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import DSMClient, DSMError, dsm_argument_spec


def get_service_status(client, name):
    """Get the current status of a service."""
    try:
        data = client.request('SYNO.Core.Service', 'get', version=1, extra_params={
            'service': json.dumps([name]),
        })
    except DSMError:
        return None

    services = data.get('services', [])
    for svc in services:
        if svc.get('name') == name or svc.get('service') == name:
            return svc
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        enabled=dict(type='bool', required=True),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']
    desired_enabled = module.params['enabled']

    client = DSMClient(module)
    client.login()

    try:
        current = get_service_status(client, name)
    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to query service {0}: {1}'.format(name, str(e)))

    if current is None:
        client.logout()
        module.fail_json(msg='Service {0} not found on this DSM device'.format(name))

    current_enabled = current.get('enabled', current.get('enable', False))
    changed = current_enabled != desired_enabled
    result = dict(name=name, enabled=desired_enabled)

    if changed and not module.check_mode:
        try:
            client.request('SYNO.Core.Service', 'set', version=1, extra_params={
                'service': json.dumps([{
                    'name': name,
                    'enabled': desired_enabled,
                }]),
            })
        except DSMError as e:
            client.logout()
            module.fail_json(msg='Failed to set service {0}: {1}'.format(name, str(e)))

    client.logout()
    module.exit_json(changed=changed, service=result)


if __name__ == '__main__':
    main()
