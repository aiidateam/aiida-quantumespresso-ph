#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
import os
from spglib import spglib
import pathlib

from aiida import load_profile
from aiida.engine import run
from aiida.orm import StructureData, load_code
from aiida.tools.data.structure import spglib_tuple_to_structure, structure_to_spglib_tuple
from ase.build import bulk

from aiida_quantumespresso.common.types import ElectronicType, RelaxType
from aiida_quantumespresso_ph.workflows.dynamical_matrix import DynamicalMatrixWorkChain

load_profile()


def test_dynamical_matrix():
    """Run a simple example of the dynamical matrix workflow."""
    structure = StructureData(ase=bulk('Si', a=5.43, cubic=True))
    cell, _, _ = structure_to_spglib_tuple(structure)
    structure = spglib_tuple_to_structure(spglib.find_primitive(cell, symprec=1e-5))
    
    pw_code = load_code('pw@localhost')
    ph_code = load_code('ph@localhost')
    overrides = {
        'clean_workdir': False,
        'relax': {
            'base': {
                'kpoints_distance': 0.6,
            }
        },
        'ph_main': {
            'kpoints_distance': 1.2,
            'ph': {
                'parameters': {
                    'INPUTPH': {
                        'epsil': True,
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
        **{'relax_type': RelaxType.NONE, 'electronic_type': ElectronicType.INSULATOR}
    )

    results, node = run.get_node(builder)
    assert node.is_finished_ok, f'{node} failed: [{node.exit_status}] {node.exit_message}'
    # diff = abs(node.outputs. ...)
    # print('Max discrepancy is: ', diff)
    # assert diff <= 1.0e-2


if __name__ == '__main__':
    test_dynamical_matrix()
