# -*- coding: utf-8 -*-
# pylint: disable=no-member,redefined-outer-name
"""Tests for the `DynamicalMatrixWorkChain` class."""
from plumpy import ProcessState
import pytest

from aiida_quantumespresso_ph.workflows.dynamical_matrix import DynamicalMatrixWorkChain as WorkChain


@pytest.fixture
def generate_workchain_dynamical_matrix(generate_workchain, generate_inputs_dynamical_matrix):
    """Generate an instance of a `DynamicalMatrixWorkChain`."""

    def _generate_workchain_dynamical_matrix(inputs=None):
        entry_point = 'quantumespresso.dynamical_matrix'

        if inputs is None:
            inputs = generate_inputs_dynamical_matrix()

        process = generate_workchain(entry_point, inputs)

        return process

    return _generate_workchain_dynamical_matrix


@pytest.fixture
def generate_scf_workchain_node(generate_structure):
    """Generate an instance of `WorkflowNode`."""

    def _generate_scf_workchain_node(exit_status=0, relax=False):
        from aiida.common import LinkType
        from aiida.orm import WorkflowNode

        node = WorkflowNode().store()
        node.set_process_state(ProcessState.FINISHED)
        node.set_exit_status(exit_status)

        if relax:
            structure = generate_structure().store()
            structure.base.links.add_incoming(node, link_type=LinkType.RETURN, link_label='output_structure')

        return node

    return _generate_scf_workchain_node


@pytest.fixture
def generate_ph_workchain_node():
    """Generate an instance of `WorkflowNode`."""

    def _generate_ph_workchain_node(exit_status=0):
        from aiida.orm import WorkflowNode

        node = WorkflowNode().store()
        node.set_process_state(ProcessState.FINISHED)
        node.set_exit_status(exit_status)

        return node

    return _generate_ph_workchain_node


@pytest.mark.usefixtures('aiida_profile')
def test_setup(generate_workchain_dynamical_matrix):
    """Test `DynamicalMatrixWorkChain.setup`."""
    process = generate_workchain_dynamical_matrix()
    process.setup()
    assert 'current_structure' in process.ctx


@pytest.mark.usefixtures('aiida_profile')
def test_should_run_relax(generate_workchain_dynamical_matrix):
    """Test `DynamicalMatrixWorkChain.should_run_relax`."""
    process = generate_workchain_dynamical_matrix()
    assert process.should_run_relax()


@pytest.mark.usefixtures('aiida_profile')
def test_run_relax(generate_workchain_dynamical_matrix):
    """Test `DynamicalMatrixWorkChain.run_relax`."""
    process = generate_workchain_dynamical_matrix()
    process.setup()
    process.run_relax()
    assert 'workchain_relax' in process.ctx


@pytest.mark.usefixtures('aiida_profile')
def test_inspect_relax(generate_workchain_dynamical_matrix, generate_scf_workchain_node):
    """Test `DynamicalMatrixWorkChain.inspect_relax`."""
    process = generate_workchain_dynamical_matrix()
    process.setup()
    process.ctx.workchain_relax = generate_scf_workchain_node(exit_status=300)
    result = process.inspect_relax()
    assert result == WorkChain.exit_codes.ERROR_SUB_PROCESS_FAILED_RELAX


@pytest.mark.usefixtures('aiida_profile')
def test_run_ph(generate_workchain_dynamical_matrix, generate_calc_job_node):
    """Test `DynamicalMatrixWorkChain.run_ph`."""
    process = generate_workchain_dynamical_matrix()

    pw_node = generate_calc_job_node(entry_point_name='quantumespresso.pw')
    process.ctx.current_folder = pw_node.outputs.remote_folder

    process.run_ph()
    assert 'workchain_ph' in process.ctx


@pytest.mark.usefixtures('aiida_profile')
def test_inspect_ph(generate_workchain_dynamical_matrix, generate_ph_workchain_node):
    """Test `DynamicalMatrixWorkChain.inspect_ph`."""
    process = generate_workchain_dynamical_matrix()
    process.setup()
    process.ctx.workchain_ph = generate_ph_workchain_node(exit_status=300)
    result = process.inspect_ph()
    assert result == WorkChain.exit_codes.ERROR_SUB_PROCESS_FAILED_PH
