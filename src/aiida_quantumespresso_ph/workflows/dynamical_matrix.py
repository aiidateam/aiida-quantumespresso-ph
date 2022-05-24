# -*- coding: utf-8 -*-
"""Workchain to compute the phonon dispersion from the raw initial unrelaxed structure."""
from aiida import orm
from aiida.common.extendeddicts import AttributeDict
from aiida.engine.processes.workchains import workchain
from aiida.plugins import WorkflowFactory, CalculationFactory
from aiida.tools.data.array.kpoints import get_explicit_kpoints_path
from aiida.engine import calcfunction, WorkChain, ToContext, if_

from aiida_quantumespresso.workflows.protocols.utils import ProtocolMixin

PhBaseWorkChain = WorkflowFactory('quantumespresso.ph.base')
PwBaseWorkChain = WorkflowFactory('quantumespresso.pw.base')
Q2rBaseWorkChain = WorkflowFactory('quantumespresso.q2r.base')
MatdynBaseWorkChain = WorkflowFactory('quantumespresso.matdyn.base')

PhCalculation = CalculationFactory('quantumespresso.ph')


class DynamicalMatrixWorkChain(ProtocolMixin, WorkChain):
    """Workchain to compute the dynamical matrix for an input structure."""

    @classmethod
    def define(cls, spec):
        """Define the work chain specification."""
        super().define(spec)

        spec.input('structure', valid_type=orm.StructureData, required=False)
        spec.input('clean_workdir', valid_type=orm.Bool, default=lambda: orm.Bool(False))
        spec.input(
            'parent_folder', valid_type=orm.RemoteData, required=False,
            help='`RemoteData` folder of a parent `pw.x` calculation.'
        )

        spec.expose_inputs(PwBaseWorkChain, namespace='pw_base', exclude=('clean_workdir', 'pw.structure'))
        spec.expose_inputs(PhBaseWorkChain, namespace='ph_base', exclude=('clean_workdir', 'ph.parent_folder'))

        spec.outline(
            cls.setup,
            if_(cls.should_run_pw)(
                cls.run_pw,
                cls.inspect_pw,
            ),
            cls.run_ph,
            cls.results,
        )

        spec.output('pw_output_parameters', valid_type=orm.Dict)
        spec.output('ph_output_parameters', valid_type=orm.Dict)
        spec.output('ph_retrieved', valid_type=orm.FolderData)

        spec.exit_code(401, 'ERROR_SUB_PROCESS_FAILED_PW',
            message='The `scf` `PwBaseWorkChain` sub process failed')

    @classmethod
    def get_protocol_filepath(cls):
        """Return ``pathlib.Path`` to the ``.yaml`` file that defines the protocols."""
        from importlib_resources import files
        from . import protocols
        return files(protocols) / 'dynamical_matrix.yaml'

    @classmethod
    def get_builder_from_protocol(cls, pw_code, ph_code, structure, protocol=None, overrides=None, **kwargs):
        """Return a builder prepopulated with inputs selected according to the chosen protocol.

        :param pw_code: the ``Code`` instance configured for the ``quantumespresso.pw`` plugin.
        :param ph_code: the ``Code`` instance configured for the ``quantumespresso.ph`` plugin.
        :param structure: the ``StructureData`` instance to use.
        :param protocol: protocol to use, if not specified, the default will be used.
        :param overrides: optional dictionary of inputs to override the defaults of the protocol.
        :param kwargs: additional keyword arguments that will be passed to the ``get_builder_from_protocol`` of all the
            sub processes that are called by this workchain.
        :return: a process builder instance with all inputs defined ready for launch.
        """
        inputs = cls.get_protocol_inputs(protocol, overrides)

        args = (pw_code, structure, protocol)
        pw_base = PwBaseWorkChain.get_builder_from_protocol(*args, overrides=inputs.get('pw_base', None), **kwargs)
        pw_base['pw'].pop('structure', None)
        pw_base.pop('clean_workdir', None)

        args = (ph_code, None, protocol)
        ph_base = PhBaseWorkChain.get_builder_from_protocol(*args, overrides=inputs.get('ph_base', None), **kwargs)
        ph_base.pop('clean_workdir', None)

        builder = cls.get_builder()
        builder.structure = structure
        builder.pw_base = pw_base
        builder.ph_base = ph_base
        builder.clean_workdir = orm.Bool(inputs['clean_workdir'])

        return builder

    def setup(self):
        """Initialise basic context variables."""
        if 'parent_folder' in self.inputs: 
            self.ctx.current_folder = self.inputs.parent_folder
        else:
            self.report('no parent given')

    def should_run_pw(self):
        """Check if the work chain should run the scf ``PwBaseWorkChain``."""
        return not 'parent_folder' in self.inputs

    def run_pw(self):
        """Run the ``PwBaseWorkChain``."""
        inputs = AttributeDict(self.inputs.pw_base)
        inputs.pw.structure = self.inputs.structure

        workchain_node = self.submit(PwBaseWorkChain, **inputs)

        self.report('launching PwBaseWorkChain<{}>'.format(workchain_node.pk))

        return ToContext(workchain_pw=workchain_node)

    def inspect_pw(self):
        """Verify that the `scf` PwBaseWorkChain finished successfully."""
        workchain = self.ctx.workchain_pw

        if not workchain.is_finished_ok:
            self.report(f'scf PwBaseWorkChain failed with exit status {workchain.exit_status}')
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_SCF

        self.ctx.current_folder = workchain.outputs.remote_folder

    def run_ph(self):
        """Run the PhWorkChain."""
        inputs = AttributeDict(self.inputs.ph_base)
        inputs.ph.parent_folder = self.ctx.current_folder

        workchain_node = self.submit(PhBaseWorkChain, **inputs)

        self.report('launching PhBaseWorkChain<{}>'.format(workchain_node.pk))

        return ToContext(workchain_ph=workchain_node)

    def results(self):
        """Attach the desired output nodes directly as outputs of the workchain."""
        self.report('workchain succesfully completed')
        self.out('pw_output_parameters', self.ctx.workchain_ph.outputs.output_parameters)
        self.out('ph_output_parameters', self.ctx.workchain_ph.outputs.merged_output_parameters) # change name ph_merged_out & add last ph
        self.out('ph_retrieved', self.ctx.workchain_ph.outputs.retrieved)
