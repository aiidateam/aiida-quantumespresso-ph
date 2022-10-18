# -*- coding: utf-8 -*-
"""Workchain to perform a ph.x calculation with optional parallelization over q-points."""
from aiida import orm
from aiida.engine import WorkChain, if_
from aiida_quantumespresso.workflows.ph.base import PhBaseWorkChain

from aiida_quantumespresso_ph.workflows.ph.parallelize_qpoints import PhParallelizeQpointsWorkChain


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
        spec.input('parallelize_qpoints', valid_type=orm.Bool, default=lambda: orm.Bool(True))
        spec.outline(
            if_(cls.should_run_parallel)(cls.run_parallel,).else_(
                cls.run_serial,
            ),
            cls.results,
        )
        spec.output('retrieved', valid_type=orm.FolderData)
        spec.output('output_parameters', valid_type=orm.Dict)

    @classmethod
    def get_builder_from_protocol(cls, code, parent_folder=None, protocol=None, overrides=None, **_):
        """Return a builder prepopulated with inputs selected according to the chosen protocol.

        :param code: the ``Code`` instance configured for the ``quantumespresso.ph`` plugin.
        :param structure: the ``StructureData`` instance to use.
        :param protocol: protocol to use, if not specified, the default will be used.
        :param overrides: optional dictionary of inputs to override the defaults of the protocol.
        :return: a process builder instance with all inputs defined ready for launch.
        """
        builder = PhBaseWorkChain.get_builder_from_protocol(
            code=code, parent_folder=parent_folder, protocol=protocol, overrides=overrides
        )

        builder._process_class = cls  # pylint: disable=protected-access

        return builder

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
        retrieved = self.ctx.workchain.outputs.retrieved
        self.out('retrieved', retrieved)
        self.out('output_parameters', self.ctx.workchain.outputs.output_parameters)
        self.report(f'workchain completed, output in {retrieved.__class__.__name__}<{retrieved.pk}>')
