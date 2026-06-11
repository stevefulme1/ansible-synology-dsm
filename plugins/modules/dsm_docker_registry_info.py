#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_docker_registry_info
short_description: List Docker registries on Synology DSM
description:
  - Retrieves a list of configured Docker container registries from a Synology DSM device.
  - This module is read-only and does not modify any settings.
  - Requires the Docker (Container Manager) package installed.
version_added: "0.5.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List all Docker registries
  stevefulme1.synology_dsm.dsm_docker_registry_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display Docker registries
  ansible.builtin.debug:
    var: result.registries
'''

RETURN = r'''
registries:
  description: List of Docker registries configured on the DSM device.
  returned: always
  type: list
  elements: dict
  sample:
    - name: "Docker Hub"
      url: "https://registry.hub.docker.com"
      verify_ssl: true
    - name: "private_registry"
      url: "https://registry.example.com"
      verify_ssl: true
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
        data = client.request('SYNO.Docker.Registry', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list Docker registries: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=False, registries=data.get('registries', []))


if __name__ == '__main__':
    main()
