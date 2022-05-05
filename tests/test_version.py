# -*- coding: utf-8 -*-
"""Tests for the :mod:`aiida_quantumespresso_ph` module."""
from packaging.version import Version, parse

import aiida_quantumespresso_ph


def test_version():
    """Test that :attr:`aiida_quantumespresso_ph.__version__` is a PEP-440 compatible version identifier."""
    assert hasattr(aiida_quantumespresso_ph, '__version__')
    assert isinstance(aiida_quantumespresso_ph.__version__, str)
    assert isinstance(parse(aiida_quantumespresso_ph.__version__), Version)
