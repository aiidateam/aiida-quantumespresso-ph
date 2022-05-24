# -*- coding: utf-8 -*-
"""Workchain to perform a ph.x calculation with optional parallelization over q-points."""
from aiida.engine import WorkChain, if_
from aiida.orm import Bool, FolderData
from aiida.plugins import WorkflowFactory

PhBaseWorkChain = WorkflowFactory('quantumespresso.ph.base')
PhParallelizeQpointsWorkChain = WorkflowFactory('quantumespresso_ph.ph.parallelize_qpoints')


class PhWorkChain(WorkChain):
    """Workchain that will run a Quantum Espresso ph.x calculation based on a previously completed pw.x calculation.

    If specified through the 'parallelize_qpoints' boolean input parameter, the calculation will be parallelized over
    the provided q-points by running the `PhParallelizeQpointsWorkChain`. Otherwise a single `PhBaseWorkChain` will be
    launched that will compute every q-point serially.
    """

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        super().define(spec)
        spec.expose_inputs(PhBaseWorkChain, exclude=('only_initialization',))
        spec.input('parallelize_qpoints', valid_type=Bool, default=lambda: Bool(True))
        spec.outline(
            if_(cls.should_run_parallel)(cls.run_parallel,).else_(
                cls.run_serial,
            ),
            cls.results,
        )
        spec.output('retrieved', valid_type=FolderData)

    def should_run_parallel(self):
        """Return whether the calculation should be parallelized over the qpoints."""
        return self.inputs.parallelize_qpoints

    def run_parallel(self):
        """Run the ``PhParallelizeQpointsWorkChain``."""
        running = self.submit(PhParallelizeQpointsWorkChain, **self.exposed_inputs(PhBaseWorkChain))
        self.report(f'running in parallel, launching PhParallelizeQpointsWorkChain<{running.pk}>')
        self.to_context(workchain=running)

    def run_serial(self):
        """Run the ``PhBaseWorkChain``."""
        running = self.submit(PhBaseWorkChain, **self.exposed_inputs(PhBaseWorkChain))
        self.report(f'running in serial, launching PhBaseWorkChain<{running.pk}>')
        self.to_context(workchain=running)

    def results(self):
        """Attach results to the workchain."""
        retrieved = self.ctx.workchain.out.retrieved
        self.out('retrieved', retrieved)
        self.report(f'workchain completed, output in {retrieved.__class__.__name__}<{retrieved.pk}>')
