#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_iscsi_target_info
short_description: List iSCSI targets on Synology DSM
description:
  - Retrieves a list of iSCSI targets configured on a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List iSCSI targets
  stevefulme1.synology_dsm.dsm_iscsi_target_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display targets
  ansible.builtin.debug:
    var: result.iscsi_targets
'''

RETURN = r'''
iscsi_targets:
  description: List of iSCSI targets.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Target name.
      type: str
      returned: always
    iqn:
      description: iSCSI Qualified Name.
      type: str
      returned: always
    status:
      description: Target status.
      type: str
      returned: always
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
        data = client.request('SYNO.Core.ISCSI.Target', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list iSCSI targets: {0}'.format(str(e)))
    finally:
        client.logout()

    targets = []
    for target in data.get('targets', []):
        targets.append(dict(
            name=target.get('name', ''),
            iqn=target.get('iqn', ''),
            status=target.get('status', ''),
        ))

    module.exit_json(changed=False, iscsi_targets=targets)


if __name__ == '__main__':
    main()
