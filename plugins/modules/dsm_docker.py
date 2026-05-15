#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_docker
short_description: Manage Docker containers on Synology DSM
description:
  - Create, delete, start, and stop Docker containers on Synology DSM.
  - Requires the Docker (Container Manager) package installed.
version_added: "0.2.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - The container name.
    type: str
    required: true
  image:
    description:
      - Docker image name and tag. Required when creating a container.
    type: str
  state:
    description:
      - Desired state of the container.
    type: str
    choices: ['present', 'absent', 'started', 'stopped']
    default: present
  ports:
    description:
      - List of port mappings in host_port:container_port format.
    type: list
    elements: str
  volumes:
    description:
      - List of volume mounts in host_path:container_path format.
    type: list
    elements: str
  env:
    description:
      - Dictionary of environment variables.
    type: dict
  restart_policy:
    description:
      - Container restart policy.
    type: str
    choices: ['no', 'always', 'on-failure', 'unless-stopped']
    default: 'no'
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Create and start a container
  stevefulme1.synology_dsm.dsm_docker:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "nginx-web"
    image: "nginx:latest"
    ports:
      - "8080:80"
    volumes:
      - "/volume1/web:/usr/share/nginx/html"
    env:
      NGINX_PORT: "80"
    restart_policy: always
    state: started

- name: Stop a container
  stevefulme1.synology_dsm.dsm_docker:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "nginx-web"
    state: stopped

- name: Remove a container
  stevefulme1.synology_dsm.dsm_docker:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    name: "nginx-web"
    state: absent
'''

RETURN = r'''
container:
  description: Details about the managed Docker container.
  returned: always
  type: dict
  contains:
    name:
      description: The container name.
      type: str
      returned: always
    state:
      description: The resulting state.
      type: str
      returned: always
    image:
      description: The container image.
      type: str
      returned: when present
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_container(client, name):
    """Find a Docker container by name."""
    data = client.request('SYNO.Docker.Container', 'list', version=1,
                          extra_params={'limit': '-1', 'offset': '0'})
    for container in data.get('containers', []):
        if container.get('name') == name:
            return container
    return None


def build_port_bindings(ports):
    """Convert port mapping strings to API format."""
    bindings = []
    for mapping in (ports or []):
        parts = mapping.split(':')
        if len(parts) == 2:
            bindings.append({
                'host_port': int(parts[0]),
                'container_port': int(parts[1]),
                'type': 'tcp',
            })
    return bindings


def build_volume_bindings(volumes):
    """Convert volume mount strings to API format."""
    bindings = []
    for mapping in (volumes or []):
        parts = mapping.split(':')
        if len(parts) >= 2:
            bindings.append({
                'host_volume_file': parts[0],
                'mount_point': parts[1],
                'type': 'rw',
            })
    return bindings


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        image=dict(type='str'),
        state=dict(
            type='str', default='present',
            choices=['present', 'absent', 'started', 'stopped'],
        ),
        ports=dict(type='list', elements='str'),
        volumes=dict(type='list', elements='str'),
        env=dict(type='dict'),
        restart_policy=dict(
            type='str', default='no',
            choices=['no', 'always', 'on-failure', 'unless-stopped'],
        ),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['image']),
            ('state', 'started', ['image'], True),
        ],
    )

    name = module.params['name']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(name=name, state=state)

    try:
        client.login()
        existing = find_container(client, name)

        if state in ('present', 'started'):
            if existing is None:
                if not module.params.get('image'):
                    module.fail_json(msg='image is required to create a container.')
                changed = True
                if not module.check_mode:
                    create_params = {
                        'name': name,
                        'additional': json.dumps({
                            'image': module.params['image'],
                            'port_bindings': build_port_bindings(module.params.get('ports')),
                            'volume_bindings': build_volume_bindings(module.params.get('volumes')),
                            'env_variables': [
                                {'key': k, 'value': v}
                                for k, v in (module.params.get('env') or {}).items()
                            ],
                            'restart_policy': module.params['restart_policy'],
                        }),
                    }
                    client.request('SYNO.Docker.Container', 'create', version=1,
                                   extra_params=create_params)
                    if state == 'started':
                        client.request('SYNO.Docker.Container', 'start', version=1,
                                       extra_params={'name': name})
                result['image'] = module.params.get('image')
            else:
                result['image'] = existing.get('image')
                if state == 'started' and existing.get('status') != 'running':
                    changed = True
                    if not module.check_mode:
                        client.request('SYNO.Docker.Container', 'start', version=1,
                                       extra_params={'name': name})

        elif state == 'stopped':
            if existing is None:
                module.fail_json(msg='Container {0} not found.'.format(name))
            if existing.get('status') == 'running':
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Docker.Container', 'stop', version=1,
                                   extra_params={'name': name})

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    if existing.get('status') == 'running':
                        client.request('SYNO.Docker.Container', 'stop', version=1,
                                       extra_params={'name': name})
                    client.request('SYNO.Docker.Container', 'delete', version=1,
                                   extra_params={'name': name})

    except DSMError as e:
        module.fail_json(msg='Docker operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, container=result)


if __name__ == '__main__':
    main()
