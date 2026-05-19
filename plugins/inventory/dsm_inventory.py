# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
name: dsm_inventory
short_description: Dynamic inventory from Synology DSM Virtual Machine Manager
description:
  - Queries VMM guests on a Synology DSM device to build inventory.
  - Groups VMs by power state (running, stopped, etc.).
  - Sets host variables for vm_id, vcpus, memory, and status.
version_added: "0.2.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  plugin:
    description:
      - The name of this plugin. Must be stevefulme1.synology_dsm.dsm_inventory.
    type: str
    required: true
    choices: ['stevefulme1.synology_dsm.dsm_inventory']
  dsm_host:
    description:
      - Hostname or IP address of the Synology DSM device.
    type: str
    required: true
  dsm_port:
    description:
      - HTTPS port for the DSM web interface.
    type: int
    default: 5001
  dsm_username:
    description:
      - Username for authenticating to DSM.
    type: str
    required: true
  dsm_password:
    description:
      - Password for authenticating to DSM.
    type: str
    required: true
    secret: true
  validate_certs:
    description:
      - Whether to validate SSL certificates.
    type: bool
    default: true
'''

EXAMPLES = r'''
# dsm_inventory.yml
plugin: stevefulme1.synology_dsm.dsm_inventory
dsm_host: "192.168.1.100"
dsm_username: "admin"
dsm_password: "secret"
'''

import json

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.parse import urlencode


class InventoryModule(BaseInventoryPlugin):
    """Dynamic inventory plugin for Synology DSM Virtual Machine Manager."""

    NAME = 'stevefulme1.synology_dsm.dsm_inventory'

    def verify_file(self, path):
        """Verify that the inventory source file is valid."""
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('.yml', '.yaml')):
                valid = True
        return valid

    def _api_request(self, base_url, api, method, version=1, sid=None,
                     extra_params=None, validate_certs=True):
        """Make a request to the Synology DSM API."""
        params = dict(
            api=api,
            version=str(version),
            method=method,
        )
        if sid:
            params['_sid'] = sid
        if extra_params:
            params.update(extra_params)

        url = '{0}/webapi/entry.cgi'.format(base_url)
        response = open_url(
            url,
            method='POST',
            data=urlencode(params),
            validate_certs=validate_certs,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        data = json.loads(response.read())

        if not data.get('success'):
            error_code = data.get('error', {}).get('code', 'unknown')
            raise AnsibleParserError(
                'DSM API error for {0}.{1} (code: {2})'.format(api, method, error_code)
            )
        return data.get('data', {})

    def _login(self, base_url, username, password, validate_certs):
        """Authenticate and return a session ID."""
        params = dict(
            api='SYNO.API.Auth',
            version='6',
            method='login',
            account=username,
            passwd=password,
            format='sid',
        )
        url = '{0}/webapi/auth.cgi'.format(base_url)
        response = open_url(
            url,
            method='POST',
            data=urlencode(params),
            validate_certs=validate_certs,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        data = json.loads(response.read())

        if not data.get('success'):
            error_code = data.get('error', {}).get('code', 'unknown')
            raise AnsibleParserError(
                'DSM login failed (error code: {0})'.format(error_code)
            )
        return data['data']['sid']

    def _logout(self, base_url, sid, validate_certs):
        """Logout from the DSM session."""
        if not sid:
            return
        try:
            self._api_request(base_url, 'SYNO.API.Auth', 'logout',
                              version=1, sid=sid, validate_certs=validate_certs)
        except Exception:
            pass

    def parse(self, inventory, loader, path, cache=True):
        """Parse the inventory source and populate inventory."""
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)

        dsm_host = self.get_option('dsm_host')
        dsm_port = self.get_option('dsm_port')
        username = self.get_option('dsm_username')
        password = self.get_option('dsm_password')
        validate_certs = self.get_option('validate_certs')

        base_url = 'https://{0}:{1}'.format(dsm_host, dsm_port)
        sid = None

        try:
            sid = self._login(base_url, username, password, validate_certs)

            data = self._api_request(
                base_url, 'SYNO.Virtualization.Guest', 'list',
                version=1, sid=sid, validate_certs=validate_certs,
                extra_params={'limit': '-1', 'offset': '0'},
            )

            for guest in data.get('guests', []):
                guest_name = guest.get('guest_name', '')
                if not guest_name:
                    continue

                self.inventory.add_host(guest_name)

                status = guest.get('status', 'unknown')
                group_name = 'vmm_{0}'.format(status)
                self.inventory.add_group(group_name)
                self.inventory.add_child(group_name, guest_name)

                self.inventory.set_variable(guest_name, 'vm_id', guest.get('guest_id'))
                self.inventory.set_variable(guest_name, 'vcpus', guest.get('vcpu_num'))
                self.inventory.set_variable(guest_name, 'memory', guest.get('vram_size'))
                self.inventory.set_variable(guest_name, 'status', status)

        except AnsibleParserError:
            raise
        except Exception as e:
            raise AnsibleParserError('Failed to query DSM VMM: {0}'.format(str(e)))
        finally:
            if sid:
                self._logout(base_url, sid, validate_certs)
