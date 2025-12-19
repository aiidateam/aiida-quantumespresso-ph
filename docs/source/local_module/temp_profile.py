# -*- coding: utf-8 -*-
"""Load and populate a temporary profile with a computer and code."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import pathlib
import shutil

from aiida import get_profile, load_ipython_extension, load_profile, manage, orm
from aiida.storage.sqlite_temp import SqliteTempBackend
from aiida_pseudo.cli.install import download_sssp
from aiida_pseudo.cli.utils import create_family_from_archive
from aiida_pseudo.groups.family import SsspConfiguration, SsspFamily
import psutil


@dataclass
class AiiDALoaded: # pylint: disable=too-many-instance-attributes
    """Dataclass for loading an AiiDA profile with predefined nodes."""
    profile: manage.Profile
    computer: orm.Computer | None
    pw_code: orm.Code | None
    ph_code: orm.Code | None
    q2r_code: orm.Code | None
    matdyn_code: orm.Code | None
    pseudos: SsspFamily | None
    structure: orm.StructureData | None
    cpu_count: int
    workdir: pathlib.Path
    pwx_path: pathlib.Path
    hwx_path: pathlib.Path


def load_temp_profile(
    name='temp_profile',
    add_computer=False,
    add_pw_code=False,
    add_ph_code=False,
    add_q2r_code=False,
    add_matdyn_code=False,
    add_sssp=False,
    debug=False,
    wipe_previous=True,
    cpu_count: int | None = None,
):
    """Load a temporary profile with a computer and code.

    This function is idempotent, so it can be called multiple times without
    creating duplicate computers and codes.

    :param name: The name of the profile to load.
    :param add_computer: Whether to add a computer to the profile.
    :param add_pw_code: Whether to add a Quantum ESPRESSO pw.x code to the profile.
    :param add_ph_code: Whether to add a Quantum ESPRESSO ph.x code to the profile.
    :param add_sssp: Whether to add the SSSP pseudopotentials to the profile.
    :param debug: Whether to enable debug mode (printing all SQL queries).
    :param wipe_previous: Whether to wipe any previous data
    """
    # load the ipython extension, if possible
    try:
        load_ipython_extension(get_ipython())
    except NameError:
        pass

    workdir_path = pathlib.Path(__file__).parent / '_aiida_workdir' / name
    repo_path = pathlib.Path(os.environ['AIIDA_PATH']) / '.aiida' / 'repository' / name

    profile = get_profile()

    if not (profile and profile.name == name):

        if wipe_previous and repo_path.exists():
            shutil.rmtree(repo_path)
        if wipe_previous and workdir_path.exists():
            shutil.rmtree(workdir_path)

        profile = SqliteTempBackend.create_profile(
            name,
            options={'runner.poll.interval': 1},
            debug=debug,
        )
        load_profile(profile, allow_switch=True)
        config = manage.get_config()
        config.add_profile(profile)

    cpu_count = cpu_count or min(4, psutil.cpu_count(logical=False))
    if not shutil.which('pw.x'):
        raise RuntimeError('pw.x not found in PATH')
    pwx_path = pathlib.Path(shutil.which('pw.x'))

    if not shutil.which('ph.x'):
        raise RuntimeError('ph.x not found in PATH')
    phx_path = pathlib.Path(shutil.which('ph.x'))

    if not shutil.which('q2r.x'):
        raise RuntimeError('q2r.x not found in PATH')
    q2rx_path = pathlib.Path(shutil.which('q2r.x'))

    if not shutil.which('matdyn.x'):
        raise RuntimeError('matdyn.x not found in PATH')
    matdynx_path = pathlib.Path(shutil.which('matdyn.x'))

    computer = load_computer(workdir_path, cpu_count) if add_computer else None
    pw_code = load_pw_code(computer, pwx_path) if (computer and add_pw_code) else None
    ph_code = load_ph_code(computer, phx_path) if (computer and add_ph_code) else None
    q2r_code = load_q2r_code(computer, q2rx_path) if (computer and add_q2r_code) else None
    matdyn_code = load_matdyn_code(computer, matdynx_path) if (computer and add_matdyn_code) else None
    pseudos = load_sssp_pseudos() if add_sssp else None
    structure = None

    return AiiDALoaded(
        profile,
        computer,
        pw_code,
        ph_code,
        q2r_code,
        matdyn_code,
        pseudos,
        structure,
        cpu_count,
        workdir_path,
        pwx_path,
        phx_path,
    )


def load_computer(work_directory: pathlib.Path, cpu_count: int):
    """Idempotent function to add the computer to the database."""
    created, computer = orm.Computer.collection.get_or_create(
        label='localhost',
        description='local computer with direct scheduler',
        hostname='localhost',
        workdir=str(work_directory.absolute()),
        transport_type='core.local',
        scheduler_type='core.direct',
    )
    if created:
        computer.store()
        computer.set_minimum_job_poll_interval(0.0)
        computer.set_default_mpiprocs_per_machine(cpu_count)
        computer.configure()
    return computer


def load_pw_code(computer, exec_path: pathlib.Path):
    """Idempotent function to add the code to the database."""
    try:
        code = orm.load_code('pw@localhost')
    except: # pylint: disable=bare-except
        code = orm.Code(
            input_plugin_name='quantumespresso.pw',
            remote_computer_exec=[computer, str(exec_path)],
        )
        code.label = 'pw'
        code.description = 'pw.x code on local computer'
        code.set_prepend_text('export OMP_NUM_THREADS=1')
        code.store()
    return code


def load_ph_code(computer, exec_path: pathlib.Path):
    """Idempotent function to add the code to the database."""
    try:
        code = orm.load_code('ph@localhost')
    except: # pylint: disable=bare-except
        code = orm.Code(
            input_plugin_name='quantumespresso.ph',
            remote_computer_exec=[computer, str(exec_path)],
        )
        code.label = 'ph'
        code.description = 'ph.x code on local computer'
        code.set_prepend_text('export OMP_NUM_THREADS=1')
        code.store()
    return code

def load_q2r_code(computer, exec_path: pathlib.Path):
    """Idempotent function to add the code to the database."""
    try:
        code = orm.load_code('q2r@localhost')
    except: # pylint: disable=bare-except
        code = orm.Code(
            input_plugin_name='quantumespresso.q2r',
            remote_computer_exec=[computer, str(exec_path)],
        )
        code.label = 'q2r'
        code.description = 'q2r.x code on local computer'
        code.set_prepend_text('export OMP_NUM_THREADS=1')
        code.store()
    return code

def load_matdyn_code(computer, exec_path: pathlib.Path):
    """Idempotent function to add the code to the database."""
    try:
        code = orm.load_code('matdyn@localhost')
    except: # pylint: disable=bare-except
        code = orm.Code(
            input_plugin_name='quantumespresso.matdyn',
            remote_computer_exec=[computer, str(exec_path)],
        )
        code.label = 'matdyn'
        code.description = 'matdyn.x code on local computer'
        code.set_prepend_text('export OMP_NUM_THREADS=1')
        code.store()
    return code

def load_sssp_pseudos(version='1.3', functional='PBEsol', protocol='efficiency'):
    """Load the SSSP pseudopotentials."""
    config = SsspConfiguration(version, functional, protocol)
    label = SsspFamily.format_configuration_label(config)

    try:
        family = orm.Group.collection.get(label=label)
    except: # pylint: disable=bare-except
        pseudos = pathlib.Path(__file__).parent / 'sssp_pseudos'
        pseudos.mkdir(exist_ok=True)

        filename = label.replace('/', '-')

        if not (pseudos / (filename + '.tar.gz')).exists():
            download_sssp(config, pseudos / (filename + '.tar.gz'), pseudos / (filename + '.json'))

        family = create_family_from_archive(
            SsspFamily,
            label,
            pseudos / (filename + '.tar.gz'),
        )
        family.set_cutoffs(
            {
                k: {i: v[i] for i in ['cutoff_wfc', 'cutoff_rho']
                    } for k, v in json.loads((pseudos / (filename + '.json')).read_text()).items()
            },
            'normal',
            unit='Ry',
        )
    return family
