# Customize inputs

## Starting from scratch

The protocols make it easier to get a starting set of inputs.
However, you can also start from an empty `builder`:

```python
pseudo_family = orm.load_group('SSSP/1.3/PBEsol/efficiency')

builder = DynamicalMatrixWorkChain.get_builder()
# ---> Setting the PwRelaxWorkChain parameters.
builder.relax.base.kpoints_distance = 0.3
builder.relax.base.pw.code = orm.load_code('pw@localhost')
builder.relax.base.pw.structure = structure
builder.relax.base.pw.pseudos = pseudo_family.get_pseudos(structure=structure)
builder.relax.base.pw.parameters = { # in this case, the geometry relaxation is skipped!
    'SYSTEM': {
        'ecutwfc': 30,
        'ecutrho': 30 * 8,
    },
    'CONTROL': {
        'calculation': 'scf'
    }
}
builder.relax.base.pw.metadata.options = {
    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 64, 'num_cores_per_mpiproc': 1}, # for SLURM scheduler only!
    'max_wallclock_seconds': 3600, # 1 hour
    'withmpi': True,
    # 'account': 'my_account_id',
    # 'queue_name': 'large_partition',
}
# ---> Setting the PhWorkChain parameters.
builder.ph_main.parallelize_qpoints = True
builder.ph_main.qpoints_distance = 0.6
builder.ph_main.ph.parameters = {
    'INPUPH': {
        'epsil': True,
        'tr2_ph': 1.0e-18,
    },
}
builder.ph_main.ph.metadata.options = {
    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 64, 'num_cores_per_mpiproc': 1}, # for SLURM scheduler only!
    'max_wallclock_seconds': 3600, # 1 hour
    'withmpi': True,
    # 'account': 'my_account_id',
    # 'queue_name': 'large_partition',
}

results = engine.run(builder)
```

You can also directly pass your inputs to the engine by preparing all of them in an `inputs` dictionary:

```python
pseudo_family = orm.load_group('SSSP/1.3/PBEsol/efficiency')

inputs = {
    'relax': {
        'base': {
            'kpoints_distance': 0.3,
            'pw': {
                'code': orm.load_code('pw@localhost'),
                'structure': structure,
                'pseudos': pseudo_family.get_pseudos(structure=structure),
                'parameters': {
                    'CONTROL': {
                        'calculation': 'scf'
                    }
                }
            }
        }
    },
    'ph_main': {
        'parallelize_qpoints': True,
        'qpoints_distance': 0.6,
        'ph': {
            'parameters': {
                'INPUTPH': {
                    'epsil': True,
                }
            }
        }
    }
}
results = engine.run(DynamicalMatrixWorkChain, **inputs)
```

## Modifying inputs given by protocols

The protocols make it easier to get a starting set of inputs. After _filling_ the builder using the protocol, you can simply modify them afterwards.

```python
builder = DynamicalMatrixWorkChain.get_builder_from_protocol(
    pw_code=orm.load_code('pw@localhost'),
    ph_code=orm.load_code('ph@localhost'),
    structure=structure,
)

# Now you can modify the pre-filled inputs
builder.relax.base.pw.parameters['SYSTEM']['ecutwfc'] = 60
builder.relax.base.pw.parameters['SYSTEM']['ecutrho'] = 60 * 8

results = engine.run(DynamicalMatrixWorkChain, **inputs)
```

### Directly overriding protocols inputs

The previous modification of protocols can be achieved also by directly overriding the values in the following way:

```python
builder = DynamicalMatrixWorkChain.get_builder_from_protocol(
    pw_code=orm.load_code('pw@localhost'),
    ph_code=orm.load_code('ph@localhost'),
    structure=structure,
    overrides={
        'relax': {
            'base': {
                'pw': {
                    'parameters': {
                        'SYSTEM': {
                            'ecutwfc': 60,
                            'ecutrho': 60 * 8,
                        }
                    }
                }
            }
        }
    }
)

results = engine.run(DynamicalMatrixWorkChain, **inputs)
```

This allows you to store the overrides in a separate file, e.g., a yaml file. This way, you can have a leaner script file, while having the input parameters in a different file for better readibility.
For instance using a yaml file called `dynmat_overrides.yaml`:

```yaml
relax:
    base:
        pw:
            parameters:
                SYSTEM:
                    ecutwfc: 60
                    ecutrho: 480
```

your script will look like:

```python
import yaml

with open('/path/to/dynmat_overrides.yaml') as handle:
    overrides = yaml.safe_load(handle)

builder = DynamicalMatrixWorkChain.get_builder_from_protocol(
    pw_code=orm.load_code('pw@localhost'),
    ph_code=orm.load_code('ph@localhost'),
    structure=structure,
    overrides=overrides
)

results = engine.run(DynamicalMatrixWorkChain, **inputs)
```

or also equivalently:

```python
from pathlib import Path

builder = DynamicalMatrixWorkChain.get_builder_from_protocol(
    pw_code=orm.load_code('pw@localhost'),
    ph_code=orm.load_code('ph@localhost'),
    structure=structure,
    overrides=Path('/path/to/dynmat_overrides.yaml')
)

results = engine.run(DynamicalMatrixWorkChain, **inputs)
```
