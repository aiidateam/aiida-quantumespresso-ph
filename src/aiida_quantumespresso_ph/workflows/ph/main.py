# -*- coding: utf-8 -*-
"""Workchain to perform a ph.x calculation with optional parallelization over q-points."""
from aiida import orm
from aiida.engine import WorkChain, if_
from aiida_quantumespresso.workflows.ph.base import PhBaseWorkChain
from aiida_quantumespresso.workflows.protocols.utils import ProtocolMixin

from aiida_quantumespresso_ph.workflows.ph.parallelize_qpoints import PhParallelizeQpointsWorkChain


class PhWorkChain(WorkChain, ProtocolMixin):
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
        spec.input('parallelize_qpoints', valid_type=orm.Bool, default=lambda: orm.Bool(False))

        spec.outline(
            if_(cls.should_run_parallel)(cls.run_parallel,).else_(
                cls.run_serial,
            ),
            cls.inspect_workchain,
            cls.results,
        )

        spec.output('retrieved', valid_type=orm.FolderData)
        spec.output('output_parameters', valid_type=orm.Dict)

        spec.exit_code(300, 'ERROR_CHILD_WORKCHAIN_FAILED', message='A child work chain failed.')

    @classmethod
    def get_protocol_filepath(cls):
        """Return ``pathlib.Path`` to the ``.yaml`` file that defines the protocols."""
        from importlib_resources import files

        from ..protocols import ph as protocols
        return files(protocols) / 'main.yaml'

    @classmethod
    def get_builder_from_protocol(
        cls, code, parent_folder=None, protocol='moderate', overrides=None, options=None, **_
    ):
        """Return a builder prepopulated with inputs selected according to the chosen protocol.

        :param code: the ``Code`` instance configured for the ``quantumespresso.ph`` plugin.
        :param structure: the ``StructureData`` instance to use.
        :param protocol: protocol to use, if not specified, the default will be used.
        :param overrides: optional dictionary of inputs to override the defaults of the protocol.
        :param options: options for computational resources
        :return: a process builder instance with all inputs defined ready for launch.
        """
        inputs = cls.get_protocol_inputs(protocol, overrides)

        data = PhBaseWorkChain.get_builder_from_protocol(  # pylint: disable=protected-access
            code=code, parent_folder=parent_folder, protocol=protocol, overrides=inputs, options=options,
        )._data

        data.pop('only_initialization', None)

        if 'parallelize_qpoints' in inputs:
            data['parallelize_qpoints'] = orm.Bool(inputs['parallelize_qpoints'])

        builder = cls.get_builder()
        builder._data = data  # pylint: disable=protected-access

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

    def inspect_workchain(self):
        """Inspect the launched ``WorkChain`` status."""
        if not self.ctx.workchain.is_finished_ok:
            self.report(f'the {self.ctx.workchain.process_label} workchain did not finish successfully')
            return self.exit_codes.ERROR_CHILD_WORKCHAIN_FAILED

    def results(self):
        """Attach results to the workchain."""
        retrieved = self.ctx.workchain.outputs.retrieved
        self.out('retrieved', retrieved)
        self.out('output_parameters', self.ctx.workchain.outputs.output_parameters)
        self.report(f'workchain completed, output in {retrieved.__class__.__name__}<{retrieved.pk}>')
