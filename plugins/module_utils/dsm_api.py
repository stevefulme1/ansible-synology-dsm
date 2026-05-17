# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json

from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.parse import urlencode


dsm_argument_spec = dict(
    dsm_host=dict(type='str', required=True),
    dsm_port=dict(type='int', default=5001),
    dsm_username=dict(type='str', required=True),
    dsm_password=dict(type='str', required=True, no_log=True),
    validate_certs=dict(type='bool', default=True),
)


class DSMError(Exception):
    """Exception raised for DSM API errors."""
    def __init__(self, message, code=None):
        super(DSMError, self).__init__(message)
        self.code = code


class DSMClient(object):
    """Client for the Synology DSM JSON-RPC style API."""

    def __init__(self, module):
        self.module = module
        self.host = module.params['dsm_host']
        self.port = module.params['dsm_port']
        self.username = module.params['dsm_username']
        self.password = module.params['dsm_password']
        self.validate_certs = module.params['validate_certs']
        self._sid = None
        self._base_url = 'https://{0}:{1}'.format(self.host, self.port)

    def login(self):
        """Authenticate to the DSM API and store the session ID."""
        params = dict(
            api='SYNO.API.Auth',
            version='6',
            method='login',
            account=self.username,
            passwd=self.password,
            format='sid',
        )
        url = '{0}/webapi/auth.cgi?{1}'.format(self._base_url, urlencode(params))
        try:
            response = open_url(
                url,
                method='GET',
                validate_certs=self.validate_certs,
            )
            data = json.loads(response.read())
        except Exception as e:
            self.module.fail_json(msg='Failed to connect to DSM at {0}: {1}'.format(self._base_url, str(e)))

        if not data.get('success'):
            error_code = data.get('error', {}).get('code', 'unknown')
            self.module.fail_json(msg='DSM login failed (error code: {0})'.format(error_code))

        self._sid = data['data']['sid']

    def logout(self):
        """Logout from the DSM API session."""
        if not self._sid:
            return
        try:
            self.request('SYNO.API.Auth', 'logout', version=1)
        except Exception:
            pass
        self._sid = None

    def request(self, api, method, version=1, extra_params=None):
        """Make an API request to DSM.

        Args:
            api: The SYNO API name (e.g. SYNO.Core.System).
            method: The API method to call.
            version: The API version number.
            extra_params: Optional dict of additional parameters.

        Returns:
            The 'data' portion of the response, or an empty dict if none.

        Raises:
            DSMError: If the API returns an error response.
        """
        params = dict(
            api=api,
            version=str(version),
            method=method,
        )
        if self._sid:
            params['_sid'] = self._sid
        if extra_params:
            params.update(extra_params)

        url = '{0}/webapi/entry.cgi'.format(self._base_url)
        try:
            response = open_url(
                url,
                method='POST',
                data=urlencode(params),
                validate_certs=self.validate_certs,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            data = json.loads(response.read())
        except Exception as e:
            raise DSMError('API request failed for {0}.{1}: {2}'.format(api, method, str(e)))

        if not data.get('success'):
            error_code = data.get('error', {}).get('code', 'unknown')
            raise DSMError(
                'API error for {0}.{1} (code: {2})'.format(api, method, error_code),
                code=error_code,
            )

        return data.get('data', {})
