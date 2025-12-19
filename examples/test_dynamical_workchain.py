#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
"""Example of how to run the dynamical matrix workflow."""
from aiida import load_profile
from aiida.engine import run
from aiida.orm import StructureData, load_code
from aiida_quantumespresso.common.types import ElectronicType, RelaxType
from ase.atoms import Atoms
import numpy as np

from aiida_quantumespresso_ph.workflows.dynamical_matrix import DynamicalMatrixWorkChain

load_profile()


def test_dynamical_matrix():
    """Run a simple example of the dynamical matrix workflow."""
    # Lattice parameter for NaCl (Angstrom)
    alat = 5.64

    # Define primitive cell vectors (in Angstrom)
    cell = alat * np.array([[0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]])

    # Fractional (scaled) positions of basis atoms in the primitive cell
    positions = [
        (0.0, 0.0, 0.0),  # Na
        (0.5, 0.5, 0.5)  # Cl
    ]

    # Corresponding atomic symbols
    symbols = ['Na', 'Cl']

    # Create the primitive NaCl structure
    nacl_primitive = Atoms(symbols=symbols, scaled_positions=positions, cell=cell, pbc=True)

    structure = StructureData(ase=nacl_primitive)

    pw_code = load_code('pw@localhost')
    ph_code = load_code('ph@localhost')
    overrides = {
        'clean_workdir': True,
        'relax': {
            'base': {
                'kpoints_distance': 0.6,
                'pw': {
                    'parameters': {
                        'SYSTEM': {
                            'ecutwfc': 40,
                            'ecutrho': 40 * 8,
                        },
                    },
                },
            },
        },
        'ph_main': {
            'parallelize_qpoints': False,
            'qpoints_distance': 1.2,
            'ph': {
                'parameters': {
                    'INPUTPH': {
                        'epsil': True,
                        'tr2_ph': 1.0e-12,
                    }
                }
            }
        }
    }

    builder = DynamicalMatrixWorkChain.get_builder_from_protocol(
        pw_code=pw_code,
        ph_code=ph_code,
        structure=structure,
        protocol='fast',
        overrides=overrides,
        **{
            'relax_type': RelaxType.NONE,
            'electronic_type': ElectronicType.INSULATOR
        }
    )

    results, node = run.get_node(builder)
    assert node.is_finished_ok, f'{node} failed: [{node.exit_status}] {node.exit_message}'

    diff = abs(results['ph_output_parameters'].dict.dielectric_constant[0][0] - 2.60)
    print('Max discrepancy is: ', diff)
    assert diff <= 1.0e-1

    diff = abs(results['ph_output_parameters'].dict.effective_charges_eu[0][0][0] - 1.11)
    print('Max discrepancy is: ', diff)
    assert diff <= 1.0e-1


if __name__ == '__main__':
    test_dynamical_matrix()
