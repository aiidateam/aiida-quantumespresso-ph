# -*- coding: utf-8 -*-
"""Tests for the ``DynamicalMatrixWorkChain.get_builder_from_protocol`` method."""
from aiida.engine import ProcessBuilder

from aiida_quantumespresso_ph.workflows.dynamical_matrix import DynamicalMatrixWorkChain


def test_get_available_protocols():
    """Test ``DynamicalMatrixWorkChain.get_available_protocols``."""
    protocols = DynamicalMatrixWorkChain.get_available_protocols()
    assert sorted(protocols.keys()) == ['fast', 'moderate', 'precise']
    assert all('description' in protocol for protocol in protocols.values())


def test_get_default_protocol():
    """Test ``DynamicalMatrixWorkChain.get_default_protocol``."""
    assert DynamicalMatrixWorkChain.get_default_protocol() == 'moderate'


def test_default(fixture_code, data_regression, serialize_builder, generate_structure):
    """Test ``DynamicalMatrixWorkChain.get_builder_from_protocol`` for the default protocol."""
    pw_code = fixture_code('quantumespresso.pw')
    ph_code = fixture_code('quantumespresso.ph')
    structure = generate_structure()

    builder = DynamicalMatrixWorkChain.get_builder_from_protocol(pw_code, ph_code, structure)

    assert isinstance(builder, ProcessBuilder)
    data_regression.check(serialize_builder(builder))
