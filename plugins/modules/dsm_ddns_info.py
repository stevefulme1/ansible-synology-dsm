#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_ddns_info
short_description: List DDNS records on Synology DSM
description:
  - Retrieves a list of Dynamic DNS records configured on a Synology DSM device.
  - This module is read-only and does not modify any settings.
version_added: "0.4.0"
author:
  - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: List DDNS records
  stevefulme1.synology_dsm.dsm_ddns_info:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
  register: result

- name: Display DDNS records
  ansible.builtin.debug:
    var: result.ddns_records
'''

RETURN = r'''
ddns_records:
  description: List of DDNS records.
  returned: always
  type: list
  elements: dict
  contains:
    hostname:
      description: DDNS hostname.
      type: str
      returned: always
    provider:
      description: DDNS provider name.
      type: str
      returned: always
    status:
      description: Record status.
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
        data = client.request('SYNO.Core.DDNS.Record', 'list', version=1)
    except DSMError as e:
        module.fail_json(msg='Failed to list DDNS records: {0}'.format(str(e)))
    finally:
        client.logout()

    records = []
    for record in data.get('records', []):
        records.append(dict(
            hostname=record.get('hostname', ''),
            provider=record.get('provider', ''),
            status=record.get('status', ''),
        ))

    module.exit_json(changed=False, ddns_records=records)


if __name__ == '__main__':
    main()
