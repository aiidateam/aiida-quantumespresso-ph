# -*- coding: utf-8 -*-
# pylint: disable=no-member,redefined-outer-name
"""Tests for the `HpWorkChain` class."""
from plumpy import ProcessState
import pytest

from aiida_quantumespresso_ph.workflows.ph.main import PhWorkChain


@pytest.fixture
def generate_workchain_main(generate_workchain, generate_inputs_ph):
    """Generate an instance of a `PhWorkChain`."""

    def _generate_workchain_main(inputs=None, qpoints=True):
        from aiida.orm import Bool

        entry_point = 'quantumespresso_ph.ph.main'

        inputs = generate_inputs_ph(inputs=inputs)
        qpoints = inputs.pop('qpoints')

        workchain_inputs = {
            'ph': inputs,
            'qpoints': qpoints,
            'parallelize_qpoints': Bool(qpoints),
        }

        process = generate_workchain(entry_point, workchain_inputs)

        return process

    return _generate_workchain_main


@pytest.fixture
def generate_ph_workchain_node(generate_calc_job_node):
    """Generate an instance of `WorkflowNode`."""

    def _generate_ph_workchain_node(exit_status=0, use_retrieved=False):
        from aiida.common import LinkType
        from aiida.orm import WorkflowNode

        node = WorkflowNode().store()
        node.set_process_state(ProcessState.FINISHED)
        node.set_exit_status(exit_status)

        # parameters = Dict({'number_of_qpoints': 2}).store()
        # parameters.base.links.add_incoming(node, link_type=LinkType.RETURN, link_label='parameters')

        if use_retrieved:
            retrieved = generate_calc_job_node(
                'quantumespresso.ph'
            ).outputs.retrieved  # otherwise the PhCalculation will complain
            retrieved.base.links.add_incoming(node, link_type=LinkType.RETURN, link_label='retrieved')

        return node

    return _generate_ph_workchain_node


@pytest.mark.usefixtures('aiida_profile')
def test_should_run_parallel(generate_workchain_main):
    """Test `HpWorkChain.should_parallelize_atoms`."""
    process = generate_workchain_main(qpoints=True)
    assert process.should_run_parallel()


@pytest.mark.usefixtures('aiida_profile')
def test_serial(generate_workchain_main):
    """Test `PhWorkChain.run_serial`."""
    process = generate_workchain_main()
    result = process.run_serial()
    assert result is None


@pytest.mark.usefixtures('aiida_profile')
def test_parallel(generate_workchain_main):
    """Test `PhWorkChain.run_serial`."""
    process = generate_workchain_main()
    result = process.run_parallel()
    assert result is None


@pytest.mark.usefixtures('aiida_profile')
def test_inspect_workchain(generate_workchain_main, generate_ph_workchain_node):
    """Test `PhWorkChain.inspect_workchain`."""
    process = generate_workchain_main()
    process.ctx.workchain = generate_ph_workchain_node(exit_status=300)

    result = process.inspect_workchain()
    assert result == PhWorkChain.exit_codes.ERROR_CHILD_WORKCHAIN_FAILED

    process.ctx.workchain = generate_ph_workchain_node(exit_status=0)
    assert process.inspect_workchain() is None
