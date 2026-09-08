# Citing

Results computed with this library rest on the model and coefficients
published by the International Transport Forum, and the packaged data is
redistributed under the OECD's terms. This page gives the citations to
use and explains what the licences allow.

**How to?**

- [Cite the model and the software](#cite-the-model-and-the-software)
- [Licence and attribution](#licence-and-attribution)
- [Where to next](#where-to-next)

## Cite the model and the software

Cite the ITF work whenever you report the numbers:

> Cazzola, P. and P. Crist (2020), *Good to Go? Assessing the Environmental
> Performance of New Mobility*, International Transport Forum, Paris.
> https://www.itf-oecd.org/good-go-assessing-environmental-performance-new-mobility

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
restate the terms; read them before redistributing the datasets
themselves, and keep the citation and the statement in anything built on
them. Results you compute with the library are your own work, for which
the citation of the source model is the requirement. Several
coefficients within the datasets originate in Argonne National
Laboratory's GREET model, which is distributed by Argonne under its own
licence; the values here come to us through the ITF workbook, and the
workbook is the source to cite for them.

This library is an adaptation of an original work by the OECD/ITF. The
opinions expressed and arguments employed in this adaptation should not be
reported as representing the official views of the OECD or of its Member
countries.

## Where to next

- [The model](model): what the cited work contains and how the library
  reproduces it.
- [Workbook audit](workbook_audit): the source's peculiarities and how
  the library treats them.
- [API reference](../reference): the public classes and functions.
