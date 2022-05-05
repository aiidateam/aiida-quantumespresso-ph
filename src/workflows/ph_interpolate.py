# -*- coding: utf-8 -*-
"""Workchain to compute the phonon dispersion from the raw initial unrelaxed structure."""
from aiida import orm
from aiida.common.extendeddicts import AttributeDict
from aiida.plugins import WorkflowFactory, CalculationFactory
from aiida.tools.data.array.kpoints import get_explicit_kpoints_path
from aiida.engine import calcfunction, WorkChain, ToContext, if_

PhBaseWorkChain = WorkflowFactory('quantumespresso.ph.base')
#PhBaseWorkChain = WorkflowFactory('kotiuga_phonon.ph.base')
PwBaseWorkChain = WorkflowFactory('quantumespresso.pw.base')
Q2rBaseWorkChain = WorkflowFactory('quantumespresso.q2r.base')
MatdynBaseWorkChain = WorkflowFactory('quantumespresso.matdyn.base')

PhCalculation = CalculationFactory('quantumespresso.ph')


class PhInterpolateWorkChain(WorkChain):
    """Workchain to compute the interpolation steps for a phonon dispersion from the already computed Dyn mat."""

    @classmethod
    def define(cls, spec):
        # yapf: disable
        super().define(spec)
        spec.input('dynmat_folder', valid_type=(orm.RemoteData,orm.FolderData), required=True,
            help='Retrieved folder containing the dynamical matrix')
        spec.expose_inputs(Q2rBaseWorkChain, namespace='q2r', exclude=('q2r.parent_folder',))
        spec.expose_inputs(MatdynBaseWorkChain, namespace='matdyn', exclude=('matdyn.force_constants',))
        spec.outline(
            cls.setup,
            cls.run_q2r,
            cls.run_matdyn,
            cls.results,
        )
        spec.output('output_parameters', valid_type=orm.Dict)
        spec.output('output_phonon_bands', valid_type=orm.BandsData)

    def setup(self):
        """Initialize context variables."""
        #self.ctx.structure = self.inputs.pw.pw.structure

    def run_q2r(self):
        """Run the Q2rCalculation."""
        inputs = AttributeDict(self.inputs.q2r)

        # Load parent folder from completed PhBaseWorkChain if not provided in inputs
        #if 'parent_folder' not in inputs:
        inputs['q2r']['parent_folder'] = self.inputs.dynmat_folder

        running = self.submit(Q2rBaseWorkChain, **inputs)

        self.report('launching Q2rBaseWorkChain<{}>'.format(running.pk))

        return ToContext(workflow_q2r=running)

    def run_matdyn(self):
        """Run the MatdynCalculation."""
        inputs = AttributeDict(self.inputs.matdyn)

        # Load parent folder from completed PhBaseWorkChain if not provided in inputs
        #if 'parent_folder' not in inputs:
        if 'force_constants' not in inputs:
            inputs['matdyn']['force_constants'] = self.ctx.workflow_q2r.outputs.force_constants

#        parameters = orm.Dict(dict={
#            'reference_distance': self.defaults.reference_distance,
#            'symprec': self.defaults.symprec,
#            'angle_tolerance': self.defaults.angle_tolerance,
#        })

        # Somehow we need to retrieve the correct structure, which is the one that is used for the
        # pw step. However, if we want to support the skipping of the pw step, we can't obtain the structure from
        # the inputs, but rather will have to obtain it from either the parent_folder input in the ph input group
        # or from the parent folder in the q2r input group if the ph step is also to be skipped. Currently it is
        # not clear how this can be done
        #structure = self.ctx.structure
        #seekpath_results = seekpath_get_explicit_kpoints_path(structure, parameters)

        #inputs['matdyn']['kpoints'] = #seekpath_results['explicit_kpoints']

        running = self.submit(MatdynBaseWorkChain, **inputs)

        self.report('launching MatdynBaseWorkChain<{}>'.format(running.pk))

        return ToContext(workflow_matdyn=running)

    def results(self):
        """Run the final step after computing the dispersion steps."""
        matdyn_calc = self.ctx.workflow_matdyn

        self.out('output_parameters', matdyn_calc.outputs.output_parameters)
        self.out('output_phonon_bands', matdyn_calc.outputs.output_phonon_bands)


@calcfunction
def seekpath_get_explicit_kpoints_path(structure, parameters):  # pylint: disable=invalid-name
    """
    Use the SeekPath wrapper to automatically generate the KpointsData path
    for the given structure and parameters
    """
    return get_explicit_kpoints_path(structure, **parameters.get_dict())
