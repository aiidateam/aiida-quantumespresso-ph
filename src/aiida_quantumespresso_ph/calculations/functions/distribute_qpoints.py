# -*- coding: utf-8 -*-
"""Calcfunction to split the q-point grid of a completed ``PhCalculation`` into individual q-points."""
from typing import Dict

from aiida.engine import calcfunction
from aiida.orm import FolderData, KpointsData
from aiida.plugins import CalculationFactory
from numpy import linalg, pi


@calcfunction
def distribute_qpoints(retrieved: FolderData) -> Dict[str, KpointsData]:
    """Split the q-point grid of a completed ``PhCalculation`` into individual q-points.

    :param retrieved: A ``FolderData`` that is the ``retrieved`` output of a ``PhCalculation``.
    :return: A dictionary of ``KpointsData`` with link labels of form ``qpoint_N`` where ``N`` is the q-point index.
    """
    # pylint: disable=too-many-locals
    PhCalculation = CalculationFactory('quantumespresso.ph')

    if not isinstance(retrieved, FolderData):
        raise TypeError(f'The retrieved argument should be a `FolderData` object, but got: {retrieved}')

    ph_calculation = retrieved.creator

    if ph_calculation.process_class != PhCalculation:
        raise ValueError(f'The `retrieved` folder creator should be a `PhCalculation`, but got: {ph_calculation}.')

    try:
        pw_calculation = ph_calculation.inputs.parent_folder.creator
    except AttributeError as exception:
        raise ValueError('Could not retrieve the `PwCalculation` preceding the `PhCalculation`.') from exception

    try:
        # If the ``PwCalculation`` has an output structure, use it
        structure = pw_calculation.outputs.output_structure
    except AttributeError:
        # Otherwise, take the input structure
        structure = pw_calculation.inputs.structure

    dynmat_prefix = PhCalculation._OUTPUT_DYNAMICAL_MATRIX_PREFIX  # pylint: disable=protected-access
    dynmat_file = f'{dynmat_prefix}0'

    with retrieved.open(dynmat_file, 'r') as handle:
        lines = handle.readlines()

    try:
        _ = [float(i) for i in lines[0].split()]
    except (IndexError, ValueError) as exception:
        raise ValueError(f'File `{dynmat_file}` does not contain the list of q-points') from exception

    cell = structure.cell
    alat = linalg.norm(cell[0])
    fact = 2. * pi / alat

    # Read q-points, converting them from 2pi/a coordinates to inverse angstrom
    qpoint_coordinates = [[float(i) * fact for i in j.split()] for j in lines[2:]]
    qpoints = {}

    for index, qpoint_coordinate in enumerate(qpoint_coordinates):
        qpoint = KpointsData()
        qpoint.set_cell(cell)
        qpoint.set_kpoints([qpoint_coordinate], cartesian=True)
        qpoints[f'qpoint_{index}'] = qpoint

    return qpoints
