# Workflow logic


## `DynamicalMatrixWorkChain`
**Purpose:** Obtain the dynamical matrix on a *q*-point grid.

The `DynamicalMatrixWorkChain` consist of three main components:

1. (optional) An initial DFT geometry optimizaiton.
2. A ground-state DFT calculation.
3. A DFPT phonon calculation, that can be parallelized over q-points.

If the initial geometry optimization completes successfully, the DFT ground-state workflow is run. Afterward, the `PhWorkChain` is executed. This workflow manages the parallel capabilities of the _PHonon_ code, meaning it can perform many simultaneous DFPT calculations (using the `PhBaseWorkChain`) for each single _q_-point.


## `PhWorkChain`
**Purpose:** Parallelize the DFPT calculation over each independent *q*-point of phonon calculation.

The `PhWorkChain` consist of two main components:

1. An initialization run to determine the independent and irreducible *q*-points.
2. A DFPT phonon calculation for each independent *q*-point.


## `PhInterpolateWorkChain`
**Purpose:** Interpolate a phonon disperion in an arbitrary path; used for obtaining phonon band structure. 

The `PhInterpolateWorkChain` consist of two main components:

1. A `q2r.x` calculation that transforms the dynamical matrix into a real space interatomic force constants (IFC) matrix.
2. A phonon band structure interpolation using `matdyn.x`, which interpolates the IFC at any arbitrary q-point.