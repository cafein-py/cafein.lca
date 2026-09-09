"""Shared checks for packaged scenarios."""

import math
import numbers


def _nonempty_text(value):
    """True for a string with non-whitespace content."""
    return isinstance(value, str) and bool(value.strip())


def _is_year(value, min_year):
    """True for a whole-number data year no earlier than ``min_year``.

    Accepts Python and NumPy integers and integer-valued floats (pandas
    upcasts the column to float64 when any row lacks a year); rejects
    strings, booleans, NaN and infinities.
    """
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        return False
    number = float(value)
    return math.isfinite(number) and number == int(number) and int(number) >= min_year


def assert_provenance_complete(scenario, min_year=2010):
    """Assert every override in ``scenario`` carries full provenance.

    Each row of :meth:`Scenario.provenance` must name a ``source`` and a
    ``note`` (non-empty strings), a ``confidence`` from the scenario
    vocabulary, and a ``year`` that is a whole number no earlier than
    ``min_year``. Parameters left at the coefficient-set default are not
    rows and so are exempt. Used to gate the European country scenarios,
    whose values are all sourced; the Indian preset, which sources some
    values and leaves others at the default, is not held to it.
    """
    problems = []
    for row in scenario.provenance().itertuples():
        where = f"{row.mode}.{row.parameter}"
        if not _nonempty_text(row.source):
            problems.append(f"{where}: source is not a non-empty string")
        if not _nonempty_text(row.confidence):
            problems.append(f"{where}: confidence is not a non-empty string")
        if not _nonempty_text(row.note):
            problems.append(f"{where}: note is not a non-empty string")
        if not _is_year(row.year, min_year):
            problems.append(
                f"{where}: year {row.year!r} is not a whole number >= {min_year}"
            )
    assert not problems, "incomplete provenance:\n" + "\n".join(problems)
