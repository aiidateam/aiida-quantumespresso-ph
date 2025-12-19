(howto-workflows-dynmat)=

# Calculate the dynamical matrix 

The `DynamicalMatrixWorkChain` is designed to compute the phonons on a _q_-point grid for a given structure using Quantum ESPRESSO's `pw.x` and `ph.x`.
It automates the complete workflow, starting from a (optionally unrelaxed) structure, exploiting the DFPT capabilities for parallelizing independent *q*-points as simultaneous `PhBaseWorkChain`.

|                     |                                                               |
|---------------------|---------------------------------------------------------------|
| Workchain class     | {class}`aiida_quantumespresso_ph.workflows.dynamitcal_matrix.DynamicalMatrixWorkChain` |
| Workchain entry point | ``quantumespresso.dynamicl_matrix``                                |

---

## Minimal example: build and submit

```python
from aiida import orm, load_profile
from aiida_quantumespresso_ph.workflows.dynamitcal_matrix import DynamicalMatrixWorkChain
from aiida.engine import submit
from ase.build import bulk

load_profile()

# Load your pw.x code and structure
pw_code = orm.load_code('pw@localhost')
ph_code = orm.load_code('ph@localhost')
structure = orm.StructureData(ase=bulk('Si', 'diamond', 5.4))

options = {
    "account": "your_account", # Change to your account if needed by your HPC provider. Otherwise, remove this line.
    "queue_name": "debug",
    "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 4}, # for SLURM scheduler
    "max_wallclock_seconds": 1800,
}

# Get a builder with sensible default parameters from a predefined protocol
builder = DynamicalMatrixWorkChain.get_builder_from_protocol(
    code=code,
    structure=structure,
    protocol="fast",  # choose from: fast, balanced, stringent
    overrides={
        'relax': {'base': {'pw': {'metadata': {'options': options}}}, 'base_scf_final': {'pw': {'metadata': {'options': options}}}},
        'ph_main': {'ph': {'metadata': {'options': options}}},
    }
)

# Submit the work chain
workchain_node = submit(builder)
print(f"Launched {workchain_node.process_label} with PK = {workchain_node.pk}")
```

The workchain will automatically:
1. Run a geometry optimization using DFT.
2. Run an SCF calculation to obtain the ground state (in principle, on more stringent parameters, cutoff, k-points, ...).
3. Run a bands calculation along the high-symmetry k-points path.

---

## Protocol details

The available protocols (See the [discussion](#protocols) for more details ) (`fast`, `balanced`, `stringent`) differ in:
- Plane-wave cutoff energies
- k-points density for DFT geometry optimization
- k-points density for DFT ground-state
- q-points density for DFPT
- Convergence thresholds

Choose `fast` for quick tests, `balanced` for production calculations, and `stringent` for high-accuracy results.
