#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_static_route
short_description: Manage static routes on Synology DSM
description:
  - Create or delete static network routes on a Synology DSM device.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  dest:
    description:
      - Destination network in CIDR notation.
    type: str
    required: true
  gateway:
    description:
      - Gateway IP address for the route.
    type: str
    required: true
  interface:
    description:
      - Network interface to use for this route.
    type: str
  state:
    description:
      - Whether the static route should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Add a static route
  stevefulme1.synology_dsm.dsm_static_route:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    dest: "10.0.0.0/8"
    gateway: "192.168.1.1"
    interface: "eth0"
    state: present

- name: Remove a static route
  stevefulme1.synology_dsm.dsm_static_route:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    dest: "10.0.0.0/8"
    gateway: "192.168.1.1"
    state: absent
'''

RETURN = r'''
static_route:
  description: Static route configuration.
  returned: always
  type: dict
  contains:
    dest:
      description: Destination network.
      type: str
      returned: always
    gateway:
      description: Gateway address.
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


def find_route(client, dest, gateway):
    """Find a static route by destination and gateway."""
    data = client.request('SYNO.Core.Network.Route.Static', 'list', version=1)
    for route in data.get('routes', []):
        if route.get('dest') == dest and route.get('gateway') == gateway:
            return route
    return None


def main():
    argument_spec = dict(
        dest=dict(type='str', required=True),
        gateway=dict(type='str', required=True),
        interface=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    dest = module.params['dest']
    gateway = module.params['gateway']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(dest=dest, gateway=gateway, state=state)

    try:
        client.login()
        existing = find_route(client, dest, gateway)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    route = {'dest': dest, 'gateway': gateway}
                    if module.params.get('interface'):
                        route['interface'] = module.params['interface']
                    client.request('SYNO.Core.Network.Route.Static', 'create',
                                   version=1, extra_params={
                                       'route': json.dumps(route),
                                   })

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    route = {'dest': dest, 'gateway': gateway}
                    client.request('SYNO.Core.Network.Route.Static', 'delete',
                                   version=1, extra_params={
                                       'route': json.dumps(route),
                                   })

    except DSMError as e:
        module.fail_json(msg='Static route operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, static_route=result)


if __name__ == '__main__':
    main()
