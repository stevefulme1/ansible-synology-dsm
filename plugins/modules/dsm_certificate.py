#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dsm_certificate
short_description: Manage SSL certificates on Synology DSM
description:
  - Import or delete SSL certificates on a Synology DSM device.
  - Can set a certificate as the system default.
version_added: "0.2.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  desc:
    description:
      - Description to identify the certificate.
    type: str
    required: true
  certificate_path:
    description:
      - Path to the certificate PEM file. Required when importing.
    type: path
  private_key_path:
    description:
      - Path to the private key PEM file. Required when importing.
    type: path
  intermediate_cert_path:
    description:
      - Path to the intermediate CA certificate PEM file.
    type: path
  as_default:
    description:
      - Whether to set this certificate as the system default.
    type: bool
    default: false
  state:
    description:
      - Whether the certificate should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.synology_dsm.dsm
'''

EXAMPLES = r'''
- name: Import an SSL certificate
  stevefulme1.synology_dsm.dsm_certificate:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    desc: "My Custom Cert"
    certificate_path: "/tmp/cert.pem"
    private_key_path: "/tmp/key.pem"
    as_default: true
    state: present

- name: Delete a certificate
  stevefulme1.synology_dsm.dsm_certificate:
    dsm_host: "192.168.1.100"
    dsm_username: "admin"
    dsm_password: "secret"
    desc: "My Custom Cert"
    state: absent
'''

RETURN = r'''
certificate:
  description: Details about the managed certificate.
  returned: always
  type: dict
  contains:
    desc:
      description: The certificate description.
      type: str
      returned: always
    id:
      description: The certificate ID on the system.
      type: str
      returned: when present
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient, DSMError, dsm_argument_spec,
)


def find_certificate(client, desc):
    """Find a certificate by its description."""
    data = client.request('SYNO.Core.Certificate.CRT', 'list', version=1)
    for cert in data.get('certificates', []):
        if cert.get('desc') == desc:
            return cert
    return None


def main():
    argument_spec = dict(
        desc=dict(type='str', required=True),
        certificate_path=dict(type='path'),
        private_key_path=dict(type='path'),
        intermediate_cert_path=dict(type='path'),
        as_default=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )
    argument_spec.update(dsm_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['certificate_path', 'private_key_path']),
        ],
    )

    desc = module.params['desc']
    state = module.params['state']

    client = DSMClient(module)
    changed = False
    result = dict(desc=desc)

    try:
        client.login()
        existing = find_certificate(client, desc)

        if state == 'present':
            if existing is None:
                changed = True
                if not module.check_mode:
                    try:
                        cert_content = open(module.params['certificate_path'], 'r').read()
                        key_content = open(module.params['private_key_path'], 'r').read()
                    except IOError as e:
                        module.fail_json(msg='Failed to read certificate files: {0}'.format(str(e)))

                    import_params = {
                        'desc': desc,
                        'as_default': str(module.params['as_default']).lower(),
                        'additional': json.dumps({
                            'cert': cert_content,
                            'key': key_content,
                        }),
                    }
                    if module.params.get('intermediate_cert_path'):
                        try:
                            inter_content = open(module.params['intermediate_cert_path'], 'r').read()
                            import_params['inter_cert'] = inter_content
                        except IOError as e:
                            module.fail_json(msg='Failed to read intermediate cert: {0}'.format(str(e)))

                    client.request('SYNO.Core.Certificate', 'import', version=1,
                                   extra_params=import_params)
            else:
                result['id'] = existing.get('id')

        elif state == 'absent':
            if existing is not None:
                changed = True
                if not module.check_mode:
                    client.request('SYNO.Core.Certificate', 'delete', version=1,
                                   extra_params={'id': existing['id']})
                result['id'] = existing.get('id')

    except DSMError as e:
        module.fail_json(msg='Certificate operation failed: {0}'.format(str(e)))
    finally:
        client.logout()

    module.exit_json(changed=changed, certificate=result)


if __name__ == '__main__':
    main()
