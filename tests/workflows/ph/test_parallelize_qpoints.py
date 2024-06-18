# -*- coding: utf-8 -*-
# pylint: disable=no-member,redefined-outer-name
"""Tests for the `PhParallelizeQpointsWorkChain` class."""
from plumpy import ProcessState
import pytest

from aiida_quantumespresso_ph.workflows.ph.parallelize_qpoints import PhParallelizeQpointsWorkChain


@pytest.fixture
def generate_workchain_qpoints(generate_workchain, generate_inputs_ph):
    """Generate an instance of a `PhParallelizeQpointsWorkChain`."""

    def _generate_workchain_qpoints(inputs=None):
        entry_point = 'quantumespresso_ph.ph.parallelize_qpoints'

        inputs = generate_inputs_ph(inputs=inputs)
        qpoints = inputs.pop('qpoints')
        process = generate_workchain(entry_point, {'ph': inputs, 'qpoints': qpoints})

        return process

    return _generate_workchain_qpoints


@pytest.fixture
def generate_ph_workchain_node(generate_calc_job_node):
    """Generate an instance of `WorkflowNode`."""

    def _generate_ph_workchain_node(exit_status=0, use_retrieved=False):
        from aiida.common import LinkType
        from aiida.orm import WorkflowNode

        node = WorkflowNode().store()
        node.set_process_state(ProcessState.FINISHED)
        node.set_exit_status(exit_status)

        if use_retrieved:
            retrieved = generate_calc_job_node(
                'quantumespresso.ph'
            ).outputs.retrieved  # otherwise the PhCalculation will complain
            retrieved.base.links.add_incoming(node, link_type=LinkType.RETURN, link_label='retrieved')

        return node

    return _generate_ph_workchain_node


@pytest.mark.usefixtures('aiida_profile')
def test_run_ph_init(generate_workchain_qpoints):
    """Test `PhParallelizeQpointsWorkChain.run_ph_init`."""
    process = generate_workchain_qpoints()
    process.run_ph_init()

    assert 'ph_init' in process.ctx


@pytest.mark.usefixtures('aiida_profile')
def test_inspect_init(generate_workchain_qpoints, generate_ph_workchain_node):
    """Test `PhParallelizeQpointsWorkChain.inspect_init`."""
    process = generate_workchain_qpoints()
    process.ctx.ph_init = generate_ph_workchain_node(exit_status=300)

    result = process.inspect_init()
    assert result == PhParallelizeQpointsWorkChain.exit_codes.ERROR_INITIALIZATION_WORKCHAIN_FAILED


@pytest.mark.usefixtures('aiida_profile')
def test_inspect_qpoints(generate_workchain_qpoints, generate_ph_workchain_node):
    """Test `PhParallelizeQpointsWorkChain.inspect_qpoints`."""
    process = generate_workchain_qpoints()
    process.ctx.workchains = [generate_ph_workchain_node(exit_status=300)]

    result = process.inspect_qpoints()
    assert result == PhParallelizeQpointsWorkChain.exit_codes.ERROR_QPOINT_WORKCHAIN_FAILED
