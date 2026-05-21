# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for DSM API client module utilities."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from unittest.mock import MagicMock, patch

from ansible_collections.stevefulme1.synology_dsm.plugins.module_utils.dsm_api import (
    DSMClient,
    DSMError,
    dsm_argument_spec,
)


class TestDSMArgumentSpec:
    """Validate the shared argument spec."""

    def test_has_required_params(self):
        assert "dsm_host" in dsm_argument_spec
        assert "dsm_username" in dsm_argument_spec
        assert "dsm_password" in dsm_argument_spec

    def test_dsm_host_required(self):
        assert dsm_argument_spec["dsm_host"]["required"] is True

    def test_dsm_password_no_log(self):
        assert dsm_argument_spec["dsm_password"]["no_log"] is True

    def test_dsm_port_default(self):
        assert dsm_argument_spec["dsm_port"]["default"] == 5001

    def test_validate_certs_default(self):
        assert dsm_argument_spec["validate_certs"]["default"] is True


class TestDSMError:
    """Validate DSMError exception."""

    def test_dsm_error_message(self):
        err = DSMError("test error")
        assert str(err) == "test error"

    def test_dsm_error_code(self):
        err = DSMError("test error", code=403)
        assert err.code == 403

    def test_dsm_error_no_code(self):
        err = DSMError("test error")
        assert err.code is None


class TestDSMClient:
    """Validate DSMClient initialization."""

    def test_client_init(self):
        module = MagicMock()
        module.params = {
            "dsm_host": "192.168.1.100",
            "dsm_port": 5001,
            "dsm_username": "admin",
            "dsm_password": "secret",
            "validate_certs": False,
        }
        client = DSMClient(module)
        assert client.host == "192.168.1.100"
        assert client.port == 5001
        assert client.username == "admin"
        assert client._sid is None

    def test_client_base_url(self):
        module = MagicMock()
        module.params = {
            "dsm_host": "nas.example.com",
            "dsm_port": 5001,
            "dsm_username": "admin",
            "dsm_password": "secret",
            "validate_certs": True,
        }
        client = DSMClient(module)
        assert "nas.example.com" in client._base_url
        assert "5001" in client._base_url
