# cafein-lca

The ITF "Good to go?" urban transport life-cycle assessment model
(Cazzola & Crist 2020) as a Python library: life-cycle energy use and
greenhouse-gas emissions per passenger-km, vehicle-km and vehicle for 56
urban transport modes, decomposed into manufacturing, delivery, use,
operational services and infrastructure.

The engine reproduces the published ITF workbook exactly — every value of
all reproducible workbook columns matches within a relative tolerance of
1e-9, enforced by the golden-master test suite. Workbook quirks found during
extraction are documented in the
[workbook audit](https://github.com/htenkanen/cafein-lca/blob/main/docs/workbook-audit.md).

```{toctree}
:maxdepth: 1
:caption: Tutorials

tutorials/quickstart
tutorials/custom-electricity-mix
```

```{toctree}
:maxdepth: 1
:caption: Reference

reference
```

## Citation

Cite the underlying model when using the numbers:

> Cazzola, P. and P. Crist (2020), *Good to Go? Assessing the Environmental
> Performance of New Mobility*, International Transport Forum, Paris.
