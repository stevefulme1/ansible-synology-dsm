# -*- coding: utf-8 -*-
"""Shared fixtures for Synology DSM unit tests."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_module():
    """Return a mock AnsibleModule."""
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "dsm_host": "192.168.1.100",
        "dsm_port": 5001,
        "dsm_username": "admin",
        "dsm_password": "secret",
        "validate_certs": False,
        "state": "present",
    }
    return module


@pytest.fixture
def mock_client():
    """Return a mock DSMClient."""
    client = MagicMock()
    client.request.return_value = {"data": {}}
    return client
