#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_docker_network
short_description: Manage Docker networks on Synology DSM
description:
  - Create or delete Docker networks on a Synology DSM device.
  - Requires the Docker (Container Manager) package installed.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the Docker network.
    type: str
    required: true
  driver:
    description:
      - Network driver to use.
    type: str
    choices: ['bridge', 'host', 'macvlan']
    default: bridge
  subnet:
    description:
      - Subnet in CIDR notation for the network.
    type: str
  gateway:
    description:
      - Gateway IP address for the network.
    type: str
  state:
    description:
      - Whether the network should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create a Docker bridge network
  stevefulme1.synology_dsm.dsm_docker_network:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "app_network"
    driver: bridge
    subnet: "172.20.0.0/16"
    gateway: "172.20.0.1"
    state: present

- name: Create a macvlan network
  stevefulme1.synology_dsm.dsm_docker_network:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "lan_network"
    driver: macvlan
    subnet: "192.168.1.0/24"
    gateway: "192.168.1.1"
    state: present

- name: Remove a Docker network
  stevefulme1.synology_dsm.dsm_docker_network:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "app_network"
    state: absent
'''

RETURN = r'''
docker_network:
  description: Docker network configuration.
  returned: always
  type: dict
  contains:
    name:
      description: Network name.
      type: str
      returned: always
    driver:
      description: Network driver.
      type: str
      returned: always
    state:
      description: Resulting state.
      type: str
      returned: always
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_network(client, name):
    """Find a Docker network by name."""
    data = client.request('SYNO.Docker.Network', 'list', version=1)
    for network in data.get('networks', []):
        if network.get('name') == name:
            return network
    return None


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        driver=dict(type='str', default='bridge', choices=['bridge', 'host', 'macvlan']),
        subnet=dict(type='str'),
        gateway=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params['name']
    state = module.params['state']
    driver = module.params['driver']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, driver=driver, state=state)

    try:
        client.login()
        existing = find_network(client, name)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    network_config = {
                        'name': name,
                        'driver': driver,
                    }
                    if module.params.get('subnet') or module.params.get('gateway'):
                        ipam = {}
                        if module.params.get('subnet'):
                            ipam['subnet'] = module.params['subnet']
                        if module.params.get('gateway'):
                            ipam['gateway'] = module.params['gateway']
                        network_config['ipam'] = {'config': [ipam]}

                    client.request('SYNO.Docker.Network', 'create', version=1,
                                   extra_params={'network': json.dumps(network_config)})

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Docker.Network', 'delete', version=1,
                                   extra_params={'name': name})

    except DSMError as e:
        module.fail_json(msg='Docker network operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, docker_network=result)


if __name__ == '__main__':
    main()
