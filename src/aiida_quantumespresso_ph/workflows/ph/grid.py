# -*- coding: utf-8 -*-
"""Workchain to perform a ``PhBaseWorkChain`` with automatic parallelization over irreps."""
from aiida import orm
from aiida.common import AttributeDict
from aiida.engine import WorkChain
from aiida.plugins import CalculationFactory, WorkflowFactory
import numpy as np

from aiida_quantumespresso_ph.calculations.functions.merge_para_ph_outputs import merge_para_ph_outputs

PhBaseWorkChain = WorkflowFactory('quantumespresso.ph.base')
distribute_qpoints = CalculationFactory('quantumespresso_ph.distribute_qpoints')
recollect_qpoints = CalculationFactory('quantumespresso_ph.recollect_qpoints')


def validate_inputs(inputs, _):
    """Validate the top level namespace."""
    parameters = inputs['ph']['parameters'].get_dict().get('INPUTHP', {})

    if not bool(is_perturb_only_atom(parameters)):
        return 'The parameters in `hp.parameters` do not specify the required key `INPUTHP.pertub_only_atom`'


class PhGridWorkChain(WorkChain):
    """Workchain to perform a ``PhBaseWorkChain`` with automatic parallelization over irreducible representations.

    This workchain differs from the ``PhParallelQpointsWorkChain`` in that the computation is parallelized over the irreducible
    representations (_irreps_). For each individual _irreps_ a separate ``PhBaseWorkChain`` is run. At the end, the computed 
    dynamical matrices of each individual workchain are collected into a single ``FolderData`` as output.
    """

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        super().define(spec)
        spec.expose_inputs(PhBaseWorkChain, exclude=('only_initialization',))
        spec.input('init_walltime', valid_type=int, default=3600, non_db=True,
            help='The walltime of the initialization `PhBaseWorkChain` in seconds (default: 3600 seconds).')
        spec.outline(
            cls.run_ph_init,
            cls.run_ph_grid,
            cls.run_ph_final,
            cls.results,
        )
        spec.output('retrieved', valid_type=orm.FolderData)
        spec.output('output_parameters', valid_type=orm.Dict)

    def run_ph_init(self):
        """Run a first dummy ``PhBaseWorkChain`` that will exit straight after initialization.

        At that point it will have generated the q-point list along with the number of _irreps_,
        which we use to determine how to distribute these over the available computational resources.
        """
        inputs = self.exposed_inputs(PhBaseWorkChain)

        # Toggle the only initialization flag and define minimal resources
        parameters = inputs['ph']['parameters'].get_dict() 
        parameters.update({'start_irr': 0, 'last_irr': 0,})
        inputs['only_initialization'] = orm.Bool(True)
        inputs['ph']['metadata']['options']['max_wallclock_seconds'] = self.inputs.init_walltime

        node = self.submit(PhBaseWorkChain, **inputs)
        self.report(f'launching initialization PhBaseWorkChain<{node.pk}>')
        self.to_context(ph_init=node)

    def run_ph_grid(self):
        """Launch individual ``PhBaseWorkChain``s for each distributed irreps for each q-point."""
        irreps_per_q = self.ctx.ph_init.outputs.output_parameters.dict.number_of_irr_representations_for_each_q
        
        inputs = AttributeDict(self.exposed_inputs(PhBaseWorkChain))
        parameters = inputs.ph.parameters.get_dict()

        for qpoint, irreps in enumerate(irreps_per_q):
            for irr in range(irreps):
                q = qpoint + 1
                i = irr + 1
                
                parameters.update({
                    'start_q': q,
                    'last_q': q,
                    'start_irr': i,
                    'last_irr': i, 
                })

                # For `epsil` == True, only the gamma point should be calculated with this setting, see
                # https://www.quantum-espresso.org/Doc/INPUT_PH.html#idm69
                dielectric = parameters.get('INPUTPH', {}).get('epsil', False) 
                if dielectric and not q == 1:
                    parameters['INPUTPH']['epsil'] = False

                raman = parameters.get('INPUTPH', {}).get('lraman', False)
                if raman and not q == 1:
                    parameters['INPUTPH']['lraman'] = False

                key = f'{q}_{i}'
                inputs.ph.parameters = orm.Dict(parameters)
                inputs.metadata.call_link_label = key

                node = self.submit(PhBaseWorkChain, **inputs)
                self.report(f'launching PhBaseWorkChain<{node.pk}> for q-point {q} and irrep {i}')
                self.to_context(**{key:node})

    def run_ph_final(self):
        """Run final `ph.x` recollecting all individual calculations."""
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
