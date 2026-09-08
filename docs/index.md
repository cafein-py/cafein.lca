# cafein.lca

Life-cycle assessment of urban passenger transport in Python: life-cycle
energy use and greenhouse-gas emissions per passenger-km, vehicle-km and
vehicle for 56 urban transport modes, decomposed into manufacturing,
delivery, use, operational services and infrastructure.

The calculation model and its default coefficients are adapted from the
life-cycle assessment model published by the International Transport Forum
with Cazzola & Crist (2020). The engine is tested against the values computed
by the source workbook: every result of all reproducible mode columns agrees
within a relative tolerance of 1e-9. Quirks of the source model found during
extraction are documented in the
[workbook audit](https://github.com/cafein-py/cafein.lca/blob/main/docs/workbook-audit.md).

```{toctree}
:maxdepth: 1
:caption: Tutorials

tutorials/quickstart
tutorials/custom-electricity-mix
tutorials/scenarios
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

This library is an adaptation of an original work by the OECD/ITF. The
opinions expressed and arguments employed in this adaptation should not be
reported as representing the official views of the OECD or of its Member
countries.
