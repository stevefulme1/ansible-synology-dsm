#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_docker_network_info
short_description: List Docker networks on Synology DSM
description:
  - Retrieves a list of Docker networks from a Synology DSM device.
  - This module is read-only and does not modify any settings.
  - Requires the Docker (Container Manager) package installed.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all Docker networks
  stevefulme1.synology_dsm.dsm_docker_network_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display Docker networks
  ansible.builtin.debug:
    var: result.networks
'''

RETURN = r'''
networks:
  description: List of Docker networks on the DSM device.
  returned: always
  type: list
  elements: dict
  sample:
    - name: "bridge"
      driver: "bridge"
      id: "abc123"
    - name: "app_network"
      driver: "bridge"
      subnet: "172.20.0.0/16"
      gateway: "172.20.0.1"
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
        data = client.request('SYNO.Docker.Network', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list Docker networks: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, networks=data.get('networks', []))


if __name__ == '__main__':
    main()
