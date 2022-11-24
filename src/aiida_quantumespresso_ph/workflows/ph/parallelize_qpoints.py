# -*- coding: utf-8 -*-
"""Workchain to perform a ``PhBaseWorkChain`` with automatic parallelization over q-points."""
from aiida import orm
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
            cls.run_distribute_qpoints,
            cls.run_ph_qgrid,
            cls.run_recollect_qpoints,
            cls.results,
        )
        spec.output('retrieved', valid_type=orm.FolderData)
        spec.output('output_parameters', valid_type=orm.Dict)

    def run_ph_init(self):
        """Run a first dummy ``PhBaseWorkChain`` that will exit straight after initialization.

        At that point it will have generated the q-point list, which we use to determine how to distribute these over
        the available computational resources.
        """
        inputs = self.exposed_inputs(PhBaseWorkChain)

        # Toggle the only initialization flag and define minimal resources
        inputs['only_initialization'] = orm.Bool(True)
        inputs['ph']['metadata']['options']['max_wallclock_seconds'] = 1800

        node = self.submit(PhBaseWorkChain, **inputs)
        self.report(f'launching initialization PhBaseWorkChain<{node.pk}>')
        self.to_context(ph_init=node)

    def run_distribute_qpoints(self):
        """Distribute the q-points."""
        self.report('launching `distribute_qpoints`')
        retrieved = self.ctx.ph_init.outputs.retrieved
        self.ctx.qpoints = distribute_qpoints(retrieved=retrieved)

    def run_ph_qgrid(self):
        """Launch individual ``PhBaseWorkChain``s for each distributed q-point."""
        inputs = self.exposed_inputs(PhBaseWorkChain)
        parameters = inputs['ph']['parameters'].get_dict()

        for _, qpoint in sorted(self.ctx.qpoints.items()):
            inputs['ph']['qpoints'] = qpoint
            # For `epsil` == True, only the gamma point should be calculated with this setting, see
            # https://www.quantum-espresso.org/Doc/INPUT_PH.html#idm69
            if parameters.get('INPUTPH', {}).get('epsil', False) and not numpy.all(qpoint.get_kpoints() == [0, 0, 0]):
                parameters['INPUTPH']['epsil'] = False
                inputs['ph']['parameters'] = orm.Dict(parameters)
            node = self.submit(PhBaseWorkChain, **inputs)
            self.report(f'launching PhBaseWorkChain<{node.pk}> for q-point<{qpoint.pk}>')
            self.to_context(workchains=append_(node))

    def run_recollect_qpoints(self):
        """Recollect the dynamical matrices from individual q-points calculations."""
        self.report('launching `recollect_qpoints`')
        retrieved_folders = {'qpoint_0': self.ctx.ph_init.outputs.retrieved}
        output_dict = {}

        for index, workchain in enumerate(self.ctx.workchains):
            ind = index + 1
            retrieved_folders[f'qpoint_{ind}'] = workchain.outputs.retrieved
            output_dict[f'output_{ind}'] = workchain.outputs.output_parameters

        self.ctx.merged_retrieved = recollect_qpoints(**retrieved_folders)
        self.ctx.merged_output_parameters = merge_para_ph_outputs(**output_dict)

    def results(self):
        """Attach the ``FolderData`` with all collected dynamical matrices as output."""
        self.out('retrieved', self.ctx.merged_retrieved)
        self.out('output_parameters', self.ctx.merged_output_parameters)
        self.report('workchain completed successfully')
