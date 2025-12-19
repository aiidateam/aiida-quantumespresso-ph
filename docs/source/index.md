---
myst:
  substitutions:
    README.md of the repository: '`README.md` of the repository'
    aiida-core documentation: '`aiida-core` documentation'
    aiida-quantumespresso-ph: '`aiida-quantumespresso-ph`'
    mapex: '[MAPEX](https://www.uni-bremen.de/en/mapex)'
    ubremen_exc: '[U Bremen Excellence Chair](https://www.uni-bremen.de/u-bremen-excellence-chairs)'
    esg: "[Excellence Strategy of Germany\u2019s federal and state governments](https://www.dfg.de/en/research_funding/excellence_strategy/index.html)"
---

```{toctree}
:hidden: true
:caption: Getting Started

get_started/installation
tutorials/index
```

```{toctree}
:hidden: true
:caption: How to

howto/run_dynmat
howto/customize_inputs
```

```{toctree}
:hidden: true
:caption: Topic guides
topics/protocol
topics/workflow_logic
```

```{toctree}
:hidden: true
:caption: Reference
reference/workflows/index
```

```{toctree}
:hidden: true

developer
```

# AiiDA Quantum ESPRESSO for PHonon

An AiiDA plugin package that provides advanced workflows for the PHonon code of the [Quantum ESPRESSO](http://www.quantumespresso.org) software suite.
Compute with maximum automation and parallelization features phonon related properties with the popular open source DFT code with automatic data provenance provided by AiiDA.

[![PyPI version](https://badge.fury.io/py/aiida-quantumespresso-ph.svg)](https://badge.fury.io/py/aiida-quantumespresso-ph)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/aiida-quantumespresso-ph.svg)](https://pypi.python.org/pypi/aiida-quantumespresso-ph)
[![Build Status](https://github.com/aiidateam/aiida-quantumespresso-ph/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aiidateam/aiida-quantumespresso-ph/actions)
[![Docs status](https://readthedocs.org/projects/aiida-quantumespresso-ph/badge)](http://aiida-quantumespresso-ph.readthedocs.io/)

______________________________________________________________________


::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} {fa}`info-circle;mr-1` Installation
:text-align: center
:shadow: md

Instructions to install, configure and setup the plugin package.

+++

```{button-ref} get_started/installation
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the installation guides
```
:::

:::{grid-item-card} {fa}`rocket;mr-1` Get started
:text-align: center
:shadow: md

Easy examples to take the first steps with the plugin package.

+++


```{button-ref} 1_dynmat
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the tutorial
```
:::
::::


## How to cite

If you use this plugin for your research, please cite the following work:

> Lorenzo Bastonero, Michele Kotiuga, Marnik Bercx, Sebastiaan P. Huber, Nicola Marzari, and Giovanni Pizzi, JOSS (2026)

Please, also cite the AiiDA related works:

> Sebastiaan P. Huber _et al._, [*AiiDA 1.0, a scalable computational infrastructure for automated reproducible workflows and data provenance*](https://doi.org/10.1038/s41597-020-00638-4), Scientific Data **7**, 300 (2020)

> Martin Uhrin, Sebastiaan. P. Huber, Jusong Yu, Nicola Marzari, and Giovanni Pizzi, [*Workflows in AiiDA: Engineering a high-throughput, event-based engine for robust and modular computational workflows*](https://www.sciencedirect.com/science/article/pii/S0010465522001746), Computational Materials Science **187**, 110086 (2021)

And do the same also for the [Quantum ESPRESSO](http://www.quantumespresso.org) code:

> Paolo Giannozzi _et al._, [*Advanced capabilities for materials modelling with Quantum ESPRESSO*](https://iopscience.iop.org/article/10.1088/1361-648X/aa8f79) J.Phys.:Condens.Matter **29**, 465901 (2017)

> Paolo Giannozzi _et al._, [*QUANTUM ESPRESSO: a modular and open-source software project for quantum simulations of materials*](https://iopscience.iop.org/article/10.1088/0953-8984/21/39/395502) J. Phys. Condens. Matter **21**, 395502 (2009)

For the GPU-enabled version of [Quantum ESPRESSO](http://www.quantumespresso.org):

> Paolo Giannozzi _et al._, [*Quantum ESPRESSO toward the exascale*](https://pubs.aip.org/aip/jcp/article/152/15/154105/1058748/Quantum-ESPRESSO-toward-the-exascale), J. Chem. Phys. **152**, 154105 (2020)


## Acknowledgements

We acknowledge support from:

:::{list-table}
:widths: 60 40
:class: logo-table
:header-rows: 0

* - The [NCCR MARVEL](http://nccr-marvel.ch/) funded by the Swiss National Science Foundation.
  - ![marvel](images/MARVEL.png)
* - The EU Centre of Excellence ["MaX – Materials Design at the Exascale"](http://www.max-centre.eu/) (Horizon 2020 EINFRA-5, Grant No. 676598).
  - ![max](images/MaX.png)
* - The [swissuniversities P-5 project "Materials Cloud"](https://www.materialscloud.org/swissuniversities)
  - ![swissuniversities](images/swissuniversities.png)
* - The {{ ubremen_exc }} program funded within the scope of the {{ esg }}.
  - ![ubremen](images/UBREMEN.png)
* - The {{ mapex }} Center for Materials and Processes.
  - ![mapex](images/MAPEX.jpg)

:::

[aiida]: http://aiida.net
[aiida quantum espresso tutorial]: https://aiida-tutorials.readthedocs.io/en/tutorial-qe-short/
[aiida-core documentation]: https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html
[aiida-quantumespresso-ph]: https://github.com/aiidateam/aiida-quantumespresso-ph
[aiidalab demo cluster]: https://aiidalab-demo.materialscloud.org/
[quantum espresso]: http://www.quantumespresso.org
[quantum mobile]: https://quantum-mobile.readthedocs.io/en/latest/index.html
