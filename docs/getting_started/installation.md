---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Installation

`cafein.lca` is a pure-Python package that depends only on numpy and
pandas. This page installs it, checks that it works, and sets up a
development environment for contributors.

**How to?**

- [Install the package](#install-the-package)
- [Verify the installation](#verify-the-installation)
- [Set up a development environment](#set-up-a-development-environment)
- [Where to next](#where-to-next)

## Install the package

Until the first release is published on PyPI, install from the
repository:

```
pip install git+https://github.com/cafein-py/cafein.lca.git
```

Once 0.1.0 is released, `pip install cafein.lca` will do the same.

The package lives in the `cafein` namespace, next to the `cafein` routing
library and `cafein.sampledata`, but it does not require either of them.
Installing `cafein.lca` alone gives you the whole life-cycle model. The
routing library is only needed if you want to attach the results to
journeys; the guide on exporting emission factors to `cafein`, planned
for a later release, will state the compatible `cafein` version and the
install command for the pair.

## Verify the installation

Import the package and ask for its version:

```{code-cell}
import cafein.lca

cafein.lca.__version__
```

The version string is the one you installed; a development install shows
a `.dev` suffix. A first calculation confirms that the packaged data
loads. This is the life-cycle greenhouse-gas result for a battery-electric
private car under the global default assumptions, in grams of
CO₂-equivalent per passenger-kilometre:

```{code-cell}
from cafein.lca import TransportLCA

lca = TransportLCA()
result = lca.calculate("private_car_bev")
round(result.ghg_per_pkm, 1)
```

If you see a number close to 125, the package and its coefficient tables
are working; the [quickstart](quickstart) explains what the number is
made of.

## Set up a development environment

To work on the package itself, clone the repository and install it in
editable mode with the development extras:

```
git clone https://github.com/cafein-py/cafein.lca.git
cd cafein.lca
pip install -e ".[dev,docs]"
pytest
```

The test suite includes a golden-master check that compares every mode
against the source model's own results. The documentation builds with
`make -C docs html`; the guides are executed during the build, so a
successful build means every output shown is current.

## Where to next

- [Quickstart](quickstart): a first calculation, explained line by line.
- [Reading results](../user_guide/reading_results): what the five
  components contain and how per-vehicle, per-vehicle-km and
  per-passenger-km results relate.
