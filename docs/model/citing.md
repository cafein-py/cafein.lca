# Citing

The library is its own implementation of an attributional transport
life-cycle assessment, but its default coefficient set is extracted from
a study published by the International Transport Forum, and results
computed with those defaults carry that study's citation with them.

**How to?**

- [Cite the model and the software](#cite-the-model-and-the-software)
- [Licence and attribution](#licence-and-attribution)
- [Where to next](#where-to-next)

## Cite the model and the software

Whenever you report numbers computed with the default coefficient set,
cite the study its coefficients come from:

> Cazzola, P. and P. Crist (2020), *Good to Go? Assessing the Environmental Performance of New Mobility*, International Transport Forum Policy Papers, Paris. https://doi.org/10.1787/f5cd236b-en

To cite the software itself, use the repository and the version you ran,
which `cafein.lca.__version__` reports:

> Tenkanen, H. *cafein.lca: Life-cycle assessment of urban passenger
> transport in Python*, version X.Y.Z. https://github.com/cafein-py/cafein.lca

Replace `X.Y.Z` with the value of `cafein.lca.__version__`.

A `CITATION.cff` file in the repository carries the same information in
machine-readable form, and each release will be archived with a DOI once
the repository is connected to Zenodo.

## Licence and attribution

The Python code is released under the MIT licence, which lets you use,
modify and redistribute it with the licence notice attached.

The MIT licence does not cover the packaged datasets. They are extracted
from the ITF workbook (© OECD/ITF 2020) and are used and adapted with
citation under the
[OECD terms and conditions](https://www.oecd.org/termsandconditions/).
Some of the coefficients originate in Argonne National Laboratory's GREET
model and reach the library through the workbook, so the workbook is the
source to cite for them.

This is an adaptation of OECD/ITF work and is not endorsed by the OECD.

If you redistribute or adapt the datasets in another tool, keep the
citation and that note. Results you compute with the library are your own
work; cite the study above for the coefficients behind the numbers.

## Where to next

- [The model](model): the method, and where the default coefficients
  come from.
- [Workbook audit](workbook_audit): the source's peculiarities and how
  the library treats them.
- [API reference](../reference): the public classes and functions.
