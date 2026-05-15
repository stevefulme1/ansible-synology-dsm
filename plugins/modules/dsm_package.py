#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_package
short_description: Manage Synology DSM packages
description:
  - Install or uninstall packages on a Synology DSM device.
  - Checks current package state before making changes to ensure idempotency.
version_added: "0.1.0"
author:
  - Steve Fulmer
options:
  name:
    description:
      - The package name to manage (e.g. "Docker", "SynologyDrive", "CloudSync").
    type: str
    required: true
  state:
    description:
      - Whether the package should be installed or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Install Docker package
  stevefulme1.synology_dsm.dsm_package:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "Docker"
    state: present

- name: Uninstall a package
  stevefulme1.synology_dsm.dsm_package:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "admin_secret"
    name: "Docker"
    state: absent
'''

RETURN = r'''
package:
  description: Details about the package that was managed.
  returned: always
  type: dict
  contains:
    name:
      description: The package name.
      type: str
      returned: always
      sample: "Docker"
    state:
      description: The resulting state of the package.
      type: str
      returned: always
      sample: "present"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import DSMClient, DSMError, dsm_argument_spec


def get_installed_packages(client):
    """Get a list of installed package names."""
    try:
        data = client.request('SYNO.Core.Package', 'list', version=2, extra_params={
            'additional': '["status"]',
        })
    except DSMError:
        return []

    packages = {}
    for pkg in data.get('packages', []):
        pkg_name = pkg.get('id') or pkg.get('name', '')
        if pkg_name:
            packages[pkg_name] = pkg
    return packages


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    client.login()

    try:
        installed = get_installed_packages(client)
    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to query packages: {0}'.format(str(e)))

    is_installed = name in installed
    changed = False
    result = dict(name=name, state=state)

    try:
        if state == 'present' and not is_installed:
            changed = True
            if not module.check_mode:
                client.request('SYNO.Core.Package', 'install', version=1, extra_params={
                    'name': name,
                })
        elif state == 'absent' and is_installed:
            changed = True
            if not module.check_mode:
                client.request('SYNO.Core.Package', 'uninstall', version=1, extra_params={
                    'name': name,
                })
    except DSMError as e:
        client.logout()
        module.fail_json(msg='Failed to manage package {0}: {1}'.format(name, str(e)))

    client.logout()
    module.exit_json(changed=changed, package=result)


if __name__ == '__main__':
    main()
