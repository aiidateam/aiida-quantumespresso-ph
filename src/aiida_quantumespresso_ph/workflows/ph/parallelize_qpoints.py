# -*- coding: utf-8 -*-
"""Workchain to perform a ``PhBaseWorkChain`` with automatic parallelization over q-points."""
from aiida import orm
from aiida.common import AttributeDict
from aiida.engine import WorkChain, append_
from aiida.plugins import CalculationFactory, WorkflowFactory
import numpy

from aiida_quantumespresso_ph.calculations.functions.merge_para_ph_outputs import merge_para_ph_outputs

PhBaseWorkChain = WorkflowFactory('quantumespresso.ph.base')
distribute_qpoints = CalculationFactory('quantumespresso_ph.distribute_qpoints')
recollect_qpoints = CalculationFactory('quantumespresso_ph.recollect_qpoints')


class PhParallelizeQpointsWorkChain(WorkChain):
    """Workchain to perform a ``PhBaseWorkChain`` with automatic parallelization over q-points.

    This workchain differs from the ``PhBaseWorkChain`` in that the computation is parallelized over the q-points. For
    each individual q-point a separate ``PhBaseWorkChain`` is run. At the end, the computed dynamical matrices of each
    individual workchain are collected into a single ``FolderData`` as output.
    """

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        super().define(spec)
        spec.expose_inputs(PhBaseWorkChain, exclude=('only_initialization',))

        spec.outline(
            cls.run_ph_init,
            cls.inspect_init,
            cls.run_distribute_qpoints,
            cls.run_ph_qgrid,
            cls.inspect_qpoints,
            cls.run_recollect_qpoints,
            cls.results,
        )

        spec.output('retrieved', valid_type=orm.FolderData)
        spec.output('output_parameters', valid_type=orm.Dict)

        spec.exit_code(300, 'ERROR_QPOINT_WORKCHAIN_FAILED', message='A child work chain failed.')
        spec.exit_code(301, 'ERROR_INITIALIZATION_WORKCHAIN_FAILED', message='The child work chain failed.')

    def run_ph_init(self):
        """Run a first dummy ``PhBaseWorkChain`` that will exit straight after initialization.

        At that point it will have generated the q-point list, which we use to determine how to distribute these over
        the available computational resources.
        """
        inputs = AttributeDict(self.exposed_inputs(PhBaseWorkChain))

        # Toggle the only initialization flag and define minimal resources
        inputs.only_initialization = orm.Bool(True)
        inputs.ph.metadata.options.max_wallclock_seconds = 1800
        inputs.metadata.call_link_label = 'phonon_initialization'

        node = self.submit(PhBaseWorkChain, **inputs)
        self.report(f'launching initialization PhBaseWorkChain<{node.pk}>')
        self.to_context(ph_init=node)

    def inspect_init(self):
        """Inspect the initialization `PhBaseWorkChain`."""
        workchain = self.ctx.ph_init

        if not workchain.is_finished_ok:
            self.report(f'initialization work chain {workchain} failed with status {workchain.exit_status}, aborting.')
            return self.exit_codes.ERROR_INITIALIZATION_WORKCHAIN_FAILED

    def run_distribute_qpoints(self):
        """Distribute the q-points."""
        self.report('launching `distribute_qpoints`')
        retrieved = self.ctx.ph_init.outputs.retrieved
        self.ctx.qpoints = distribute_qpoints(retrieved=retrieved)

    def run_ph_qgrid(self):
        """Launch individual ``PhBaseWorkChain``s for each distributed q-point."""
        inputs = AttributeDict(self.exposed_inputs(PhBaseWorkChain))
        parameters = inputs.ph.parameters.get_dict()

        for q_point_key, qpoint in sorted(self.ctx.qpoints.items()):
            inputs.qpoints = qpoint

            # For `epsil` == True, only the gamma point should be calculated with this setting, see
            # https://www.quantum-espresso.org/Doc/INPUT_PH.html#idm69
            if parameters.get('INPUTPH', {}).get('epsil', False) and not numpy.all(qpoint.get_kpoints() == [0, 0, 0]):
                parameters['INPUTPH']['epsil'] = False
                inputs.ph.parameters = orm.Dict(parameters)

            inputs.metadata.call_link_label = q_point_key

            node = self.submit(PhBaseWorkChain, **inputs)
            self.report(f'launching PhBaseWorkChain<{node.pk}> for q-point {q_point_key.split("_")[-1]} <{qpoint.pk}>')
            self.to_context(workchains=append_(node))

    def inspect_qpoints(self):
        """Inspect each parallel qpoint `PhBaseWorkChain`."""
        for workchain in self.ctx.workchains:
            if not workchain.is_finished_ok:
                self.report(f'child work chain {workchain} failed with status {workchain.exit_status}, aborting.')
                return self.exit_codes.ERROR_QPOINT_WORKCHAIN_FAILED

    def run_recollect_qpoints(self):
        """Recollect the dynamical matrices from individual q-points calculations."""
        self.report('launching `recollect_qpoints`')
        retrieved_folders = {'qpoint_0': self.ctx.ph_init.outputs.retrieved}
        output_dict = {}

        for index, workchain in enumerate(self.ctx.workchains):
            ind = index + 1
            retrieved_folders[f'qpoint_{ind}'] = workchain.outputs.retrieved
            output_dict[f'output_{ind}'] = workchain.outputs.output_parameters

        retrieved_folders['metadata'] = {'call_link_label': 'recollect_qpoints'}

        self.ctx.merged_retrieved = recollect_qpoints(**retrieved_folders)
        self.ctx.merged_output_parameters = merge_para_ph_outputs(**output_dict)

    def results(self):
        """Attach the ``FolderData`` with all collected dynamical matrices as output."""
        self.out('retrieved', self.ctx.merged_retrieved)
        self.out('output_parameters', self.ctx.merged_output_parameters)
        self.report('workchain completed successfully')
