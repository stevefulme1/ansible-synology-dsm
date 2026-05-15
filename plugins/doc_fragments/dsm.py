# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r'''
options:
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
  validate_certs:
    description:
      - Whether to validate SSL certificates when connecting to DSM.
    type: bool
    default: false
'''
