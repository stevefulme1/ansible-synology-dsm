# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for dsm_package module."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible_collections.stevefulme1.synology_dsm.plugins.modules import dsm_package


class TestDocumentation:
    """Validate module documentation strings."""

    def test_documentation_exists(self):
        assert hasattr(dsm_package, "DOCUMENTATION")
        assert len(dsm_package.DOCUMENTATION) > 0

    def test_documentation_has_module_name(self):
        assert "dsm_package" in dsm_package.DOCUMENTATION

    def test_documentation_has_short_description(self):
        assert "short_description" in dsm_package.DOCUMENTATION

    def test_documentation_has_options(self):
        assert "options" in dsm_package.DOCUMENTATION

    def test_examples_exist(self):
        assert hasattr(dsm_package, "EXAMPLES")
        assert len(dsm_package.EXAMPLES) > 0

    def test_examples_contain_fqcn(self):
        assert "stevefulme1.synology_dsm" in dsm_package.EXAMPLES

    def test_return_exists(self):
        assert hasattr(dsm_package, "RETURN")
        assert len(dsm_package.RETURN) > 0


class TestMainFunction:
    """Validate main function exists and is callable."""

    def test_main_exists(self):
        assert hasattr(dsm_package, "main")
        assert callable(dsm_package.main)

    def test_module_has_name_guard(self):
        """Verify the module has if __name__ == __main__ guard."""
        import inspect
        source = inspect.getsource(dsm_package)
        assert 'if __name__ == "__main__"' in source or "if __name__ == '__main__'" in source
