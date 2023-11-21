# -*- coding: utf-8 -*-
"""Tests for the ``PhWorkChain.get_builder_from_protocol`` method."""
from aiida.engine import ProcessBuilder

from aiida_quantumespresso_ph.workflows.ph.main import PhWorkChain


def test_get_available_protocols():
    """Test ``PhWorkChain.get_available_protocols``."""
    protocols = PhWorkChain.get_available_protocols()
    assert sorted(protocols.keys()) == ['fast', 'moderate', 'precise']
    assert all('description' in protocol for protocol in protocols.values())


def test_get_default_protocol():
    """Test ``PhWorkChain.get_default_protocol``."""
    assert PhWorkChain.get_default_protocol() == 'moderate'


def test_default(fixture_code, data_regression, serialize_builder):
    """Test ``PhWorkChain.get_builder_from_protocol`` for the default protocol."""
    code = fixture_code('quantumespresso.ph')

    builder = PhWorkChain.get_builder_from_protocol(code)

    assert isinstance(builder, ProcessBuilder)
    data_regression.check(serialize_builder(builder))


def test_parent_scf_folder(fixture_code, generate_calc_job_node):
    """Test ``PhWorkChain.get_builder_from_protocol`` with ``parent_scf_folder`` keyword."""
    code = fixture_code('quantumespresso.ph')
    parent_scf_folder = generate_calc_job_node('quantumespresso.pw').outputs.remote_folder

    builder = PhWorkChain.get_builder_from_protocol(code, parent_folder=parent_scf_folder)
    assert builder.ph.parent_folder == parent_scf_folder  # pylint: disable=no-member


def test_options(fixture_code):
    """Test specifying ``options`` for the ``get_builder_from_protocol()`` method."""
    code = fixture_code('quantumespresso.ph')

    queue_name = 'super-fast'
    withmpi = False  # The protocol default is ``True``

    options = {'queue_name': queue_name, 'withmpi': withmpi}
    builder = PhWorkChain.get_builder_from_protocol(code, options=options)

    assert builder.ph.metadata['options']['queue_name'] == queue_name  # pylint: disable=no-member
