# -*- coding: utf-8 -*-
"""merge data from mulitple ph runs called by one PhBase."""
from aiida import orm
from aiida.engine import calcfunction


@calcfunction
def merge_para_ph_outputs(**kwargs):
    """Calcfunction to merge outputs from multiple parallelized `ph.x` calculations with different q-points."""

    # Get the outputs, sorted by label
    outputs = [el[1].get_dict() for el in sorted(list(kwargs.items()), key=lambda l: l[0])]

    merged = {}

    total_walltime = 0
    number_irreps = []

    for index, output in enumerate(outputs):

        total_walltime += output.pop('wall_time_seconds', 0)
        number_irreps.extend(output.pop('number_of_irr_representations_for_each_q', []))
        merged[f'dynamical_matrix_{index + 1}'] = output.pop('dynamical_matrix_1')

        for key, value in output.items():
            merged[key] = value

    merged['wall_time_seconds'] = total_walltime
    merged['number_of_irr_representations_for_each_q'] = number_irreps
    merged['number_of_qpoints'] = len(outputs)

    return orm.Dict(dict=merged)
