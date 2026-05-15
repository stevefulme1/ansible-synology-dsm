#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_docker_registry
short_description: Manage Docker registries on Synology DSM
description:
  - Add, update, or remove Docker container registries on a Synology DSM device.
  - Requires the Docker (Container Manager) package installed.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name for the registry entry.
    type: str
    required: true
  url:
    description:
      - Registry URL. Required when creating a registry.
    type: str
  username:
    description:
      - Registry authentication username.
    type: str
  password:
    description:
      - Registry authentication password.
    type: str
  verify_ssl:
    description:
      - Whether to verify SSL certificates for this registry.
    type: bool
    default: true
  state:
    description:
      - Whether the registry should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Add a private Docker registry
  stevefulme1.synology_dsm.dsm_docker_registry:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "private_registry"
    url: "https://registry.example.com"
    username: "reguser"
    password: "regpass"
    verify_ssl: true
    state: present

- name: Remove a registry
  stevefulme1.synology_dsm.dsm_docker_registry:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "private_registry"
    state: absent
'''

RETURN = r'''
docker_registry:
  description: Docker registry configuration.
  returned: always
  type: dict
  contains:
    name:
      description: Registry name.
      type: str
      returned: always
    url:
      description: Registry URL.
      type: str
      returned: when present
    state:
      description: Resulting state.
      type: str
      returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_registry(client, name):
    """Find a Docker registry by name."""
    data = client.request('SYNO.Docker.Registry', 'list', version=1)
    for registry in data.get('registries', []):
        if registry.get('name') == name:
            return registry
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        url=dict(type='str'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        verify_ssl=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['url']),
        ],
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        existing = find_registry(client, name)

        if state == 'present':
            result['url'] = module.params['url']
            if existing is None:
                changed = True
                if not module.check_mode:
                    params = {
                        'name': name,
                        'url': module.params['url'],
                        'verify_ssl': str(module.params['verify_ssl']).lower(),
                    }
                    if module.params.get('username'):
                        params['username'] = module.params['username']
                    if module.params.get('password'):
                        params['password'] = module.params['password']
                    client.request('SYNO.Docker.Registry', 'create', version=1,
                                   extra_params=params)
            else:
                needs_update = (
                    existing.get('url') != module.params['url']
                    or existing.get('verify_ssl') != module.params['verify_ssl']
                )
                if needs_update:
                    changed = True
                    if not module.check_mode:
                        params = {
                            'name': name,
                            'url': module.params['url'],
                            'verify_ssl': str(module.params['verify_ssl']).lower(),
                        }
                        if module.params.get('username'):
                            params['username'] = module.params['username']
                        if module.params.get('password'):
                            params['password'] = module.params['password']
                        client.request('SYNO.Docker.Registry', 'set', version=1,
                                       extra_params=params)

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Docker.Registry', 'delete', version=1,
                                   extra_params={'name': name})

    except DSMError as e:
        module.fail_json(msg='Docker registry operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, docker_registry=result)


if __name__ == '__main__':
    main()
