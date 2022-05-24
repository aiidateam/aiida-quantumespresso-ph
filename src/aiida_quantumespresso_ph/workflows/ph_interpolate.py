# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""Workchain to compute the phonon dispersion from the raw initial unrelaxed structure."""
from aiida import orm
from aiida.common.extendeddicts import AttributeDict
from aiida.engine import ToContext, WorkChain
from aiida.plugins import CalculationFactory, WorkflowFactory

PhBaseWorkChain = WorkflowFactory('quantumespresso.ph.base')
PwBaseWorkChain = WorkflowFactory('quantumespresso.pw.base')
Q2rBaseWorkChain = WorkflowFactory('quantumespresso.q2r.base')
MatdynBaseWorkChain = WorkflowFactory('quantumespresso.matdyn.base')

PhCalculation = CalculationFactory('quantumespresso.ph')


class PhInterpolateWorkChain(WorkChain):
    """Workchain to compute the interpolation steps for a phonon dispersion from the already computed Dyn mat."""

    @classmethod
    def define(cls, spec):
        """Define the work chain specification."""
        super().define(spec)
        spec.input(
            'dynmat_folder',
            valid_type=(orm.RemoteData, orm.FolderData),
            required=True,
            help='Retrieved folder containing the dynamical matrix'
        )
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

        self.report(f'launching Q2rBaseWorkChain<{running.pk}>')

        return ToContext(workflow_q2r=running)

    def run_matdyn(self):
        """Run the MatdynCalculation."""
        inputs = AttributeDict(self.inputs.matdyn)

        # Load parent folder from completed PhBaseWorkChain if not provided in inputs
        if 'force_constants' not in inputs:
            inputs['matdyn']['force_constants'] = self.ctx.workflow_q2r.outputs.force_constants

        running = self.submit(MatdynBaseWorkChain, **inputs)

        self.report(f'launching MatdynBaseWorkChain<{running.pk}>')

        return ToContext(workflow_matdyn=running)

    def results(self):
        """Run the final step after computing the dispersion steps."""
        matdyn_calc = self.ctx.workflow_matdyn

        self.out('output_parameters', matdyn_calc.outputs.output_parameters)
        self.out('output_phonon_bands', matdyn_calc.outputs.output_phonon_bands)
