from aiida import orm
from aiida.engine import WorkChain, ToContext

from .dynamical_matrix import DynamicalMatrixWorkChain
from .ph_interpolate import PhInterpolateWorkChain

class PhononBandsWorkChain(WorkChain):
    """
    WorkChain to compute Phonon Bands starting from a structure.
    Wraps DynamicalMatrixWorkChain (SCF + PH) and PhInterpolateWorkChain (Q2R + Matdyn).
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # Expose inputs from sub-workchains
        spec.expose_inputs(DynamicalMatrixWorkChain, namespace='dynamical_matrix')
        spec.expose_inputs(PhInterpolateWorkChain, namespace='interpolate', exclude=('dynmat_folder',))

        spec.outline(
            cls.run_dynamical_matrix,
            cls.run_interpolate,
            cls.results,
        )

        spec.output('output_phonon_bands', valid_type=orm.BandsData)
        spec.output('output_parameters', valid_type=orm.Dict)

        spec.exit_code(401, 'ERROR_SUB_PROCESS_FAILED_DYNAMICAL_MATRIX', message='The DynamicalMatrixWorkChain sub process failed')
        spec.exit_code(402, 'ERROR_SUB_PROCESS_FAILED_INTERPOLATE', message='The PhInterpolateWorkChain sub process failed')

    def run_dynamical_matrix(self):
        inputs = self.exposed_inputs(DynamicalMatrixWorkChain, namespace='dynamical_matrix')
        running = self.submit(DynamicalMatrixWorkChain, **inputs)
        self.report(f'Submitted DynamicalMatrixWorkChain<{running.pk}>')
        return ToContext(dynamical_matrix=running)

    def run_interpolate(self):
        dynamical_matrix = self.ctx.dynamical_matrix
        if not dynamical_matrix.is_finished_ok:
            self.report(f'DynamicalMatrixWorkChain failed with status {dynamical_matrix.exit_status}')
            return self.exit_codes.ERROR_SUB_PROCESS_FAILED_DYNAMICAL_MATRIX

        inputs = self.exposed_inputs(PhInterpolateWorkChain, namespace='interpolate')
        # Connect outputs
        inputs['dynmat_folder'] = dynamical_matrix.outputs.ph_retrieved
        
        running = self.submit(PhInterpolateWorkChain, **inputs)
        self.report(f'Submitted PhInterpolateWorkChain<{running.pk}>')
        return ToContext(interpolate=running)

    def results(self):
        interpolate = self.ctx.interpolate
        if not interpolate.is_finished_ok:
             self.report(f'PhInterpolateWorkChain failed with status {interpolate.exit_status}')
             return self.exit_codes.ERROR_SUB_PROCESS_FAILED_INTERPOLATE

        self.out('output_phonon_bands', interpolate.outputs.output_phonon_bands)
        self.out('output_parameters', interpolate.outputs.output_parameters)
        self.report('PhononBandsWorkChain finished successfully')
