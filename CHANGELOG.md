# Changelog

All notable changes to **stevefulme1.synology_dsm** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2026-05-18

### Security

- Move login password from GET query string to POST request body in `dsm_api.py` and `dsm_inventory.py`
- Add `no_log=True` to SNMP community string parameter in `dsm_snmp.py`
- Expand `.gitignore` to exclude secrets, credentials, and IDE files

## [2.0.0] - 2026-05-15

### Added

- GPL-3.0 license file
- Pre-commit and linting configuration
- Role README.md files for Galaxy import compliance

### Changed

- Default `validate_certs` to `True` for security hardening

### Fixed

- Resolve CI workflow failures
- Add role README.md files required by Galaxy importer

## [1.1.0] - 2026-05-15

### Added

- 23 read-only info modules for full DSM coverage
- 2 EDA source plugins for event-driven automation
- 10 Day-2 operation roles (backup, certificate, docker, firmware, monitoring, network, security, storage, system, user)
- Total: 93 modules, 10 roles, full EDA/inventory coverage

### Fixed

- Invalid variable name in `dsm_2fa_info` module

## [1.0.0] - 2026-05-15

### Added

- 30 modules covering file station, security, backup, network, storage, monitoring, and Docker
- TrueNAS parity modules and info modules (27 new)
- Tier-2/3 modules for snapshots, backup, certs, firewall, Docker, and VMM
- DSM API client and core modules
- CI workflow with auto-merge for owner PRs

## [0.1.0] - 2026-05-15

### Added

- Initial project scaffolding with SECURITY.md, CONTRIBUTING.md
- Unit test framework
