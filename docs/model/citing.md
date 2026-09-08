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

The packaged datasets are a different matter, and the MIT licence does
not cover them. They are extracted from the ITF workbook, © OECD/ITF
2020, and are used and adapted here with citation under the
[OECD terms and conditions](https://www.oecd.org/termsandconditions/),
following the two conditions those terms attach to adaptations: the
source is cited, and the adaptation carries the statement below that it
does not represent the views of the OECD. This documentation does not
restate the terms. If you redistribute or adapt the packaged datasets
themselves, for example by shipping them in another tool, read the terms
and keep both the citation and the statement. If you
publish results computed with the library, they are your own work: cite
the study above because its coefficients are behind the numbers; the
statement is not required for results, and the library's own statement
already covers the packaged adaptation. Several
coefficients within the datasets originate in Argonne National
Laboratory's GREET model, which is distributed by Argonne under its own
licence; the values here come to us through the ITF workbook, and the
workbook is the source to cite for them.

This library is an adaptation of an original work by the OECD/ITF. The
opinions expressed and arguments employed in this adaptation should not be
reported as representing the official views of the OECD or of its Member
countries.

## Where to next

- [The model](model): the method, and where the default coefficients
  come from.
- [Workbook audit](workbook_audit): the source's peculiarities and how
  the library treats them.
- [API reference](../reference): the public classes and functions.
