"""Scenario bundles: named sets of per-mode parameter overrides.

A scenario is a TOML document::

    name = "my_city"
    description = "..."
    power_mix = "India"                 # preset, shares table, or per case

    [modes.bus_ice]
    lifetime_years = 12                 # scalar, no provenance

    [modes."bus_*".occupancy]           # glob pattern over mode slugs
    best = 92
    central = 53
    worst = 25
    evidence = "model_input"
    geography = "Mumbai Metropolitan Region"
    source = "Shinde et al. 2019, Table 7"
    confidence = "medium"
    note = "operating-condition inputs of a Mumbai LCA"

The three cases ``best``, ``central`` and ``worst`` are named by their
effect on emissions per pkm. A parameter is a scalar, a table with ``value``
(scalar with provenance), or a table with the three cases; ``evidence``,
``geography`` and ``source`` may themselves be per-case tables.
``power_mix`` is a packaged preset name, a table of the six generation
shares, or a per-case table of either. Exact slugs take precedence over glob
patterns.
"""

import dataclasses
import fnmatch
import pathlib
import sys

from .modes import CANONICAL_MODES, mode

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

CASES = ("best", "central", "worst")
EVIDENCE = (
    "observed",
    "model_input",
    "capacity",
    "projection",
    "derived",
    "assumption",
)
CONFIDENCE = ("high", "medium", "low")
PROVENANCE_KEYS = ("evidence", "geography", "source", "confidence", "note")
PACKAGED_DIR = pathlib.Path(__file__).parent / "data" / "scenarios"
_GLOB_CHARS = set("*?[")


def _pick(value, case, where):
    """Resolve a scalar-or-cases value for ``case``."""
    if not isinstance(value, dict):
        return value
    if set(value) != set(CASES):
        raise ValueError(
            f"{where}: a case table needs exactly the keys "
            f"{', '.join(CASES)}; got {', '.join(sorted(value))}"
        )
    return value[case]


def _entry(spec, case, where):
    """Resolve one parameter spec to (value, provenance dict)."""
    if not isinstance(spec, dict):
        return spec, {}
    meta = {k: spec[k] for k in PROVENANCE_KEYS if k in spec}
    values = {k: v for k, v in spec.items() if k not in PROVENANCE_KEYS}
    value = values["value"] if set(values) == {"value"} else _pick(values, case, where)
    for key in ("evidence", "geography", "source"):
        if key in meta:
            meta[key] = _pick(meta[key], case, f"{where}.{key}")
    if meta.get("evidence") not in (None, *EVIDENCE):
        raise ValueError(f"{where}.evidence must be one of {', '.join(EVIDENCE)}")
    if meta.get("confidence") not in (None, *CONFIDENCE):
        raise ValueError(f"{where}.confidence must be one of {', '.join(CONFIDENCE)}")
    return value, meta


def _resolve_modes(table, case):
    exact, patterns = {}, {}
    for key, params in table.items():
        if not isinstance(params, dict):
            raise ValueError(f"[modes.{key}] must be a table of parameters")
        picked = {n: _entry(v, case, f"modes.{key}.{n}") for n, v in params.items()}
        if _GLOB_CHARS & set(key):
            matches = fnmatch.filter(CANONICAL_MODES, key)
            if not matches:
                raise KeyError(f"mode pattern '{key}' matches no mode")
            for slug in matches:
                patterns.setdefault(slug, {}).update(picked)
        elif key not in CANONICAL_MODES:
            raise KeyError(f"unknown mode '{key}' in scenario")
        else:
            exact.setdefault(key, {}).update(picked)
    overrides, provenance = {}, {}
    for slug in patterns.keys() | exact.keys():
        merged = {**patterns.get(slug, {}), **exact.get(slug, {})}
        overrides[slug] = {n: v for n, (v, _) in merged.items()}
        provenance[slug] = {n: m for n, (_, m) in merged.items()}
        mode(slug).replace(**overrides[slug])  # validates names and ranges
    return overrides, provenance


@dataclasses.dataclass(frozen=True)
class Scenario:
    """A named bundle of parameter overrides and an electricity mix.

    Build one with :meth:`load`; ``overrides`` maps canonical mode slugs to
    the parameter values of the selected ``case`` and ``provenance_records``
    to their evidence fields (see :meth:`provenance`).
    """

    name: str
    case: str = "central"
    power_mix: object = None
    overrides: dict = dataclasses.field(default_factory=dict)
    description: str = ""
    provenance_records: dict = dataclasses.field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, path, case="central"):
        """Load a scenario for one of the three cases.

        ``path`` is a TOML file or the name of a packaged scenario (see
        :func:`list_scenarios`).
        """
        if case not in CASES:
            raise ValueError(f"case must be one of {', '.join(CASES)}, got {case!r}")
        path = _locate(path)
        with open(path, "rb") as f:
            doc = tomllib.load(f)
        unknown = set(doc) - {"name", "description", "power_mix", "modes"}
        if unknown:
            raise ValueError(f"unknown top-level keys: {', '.join(sorted(unknown))}")
        power_mix = doc.get("power_mix")
        if isinstance(power_mix, dict) and set(power_mix) <= set(CASES):
            power_mix = _pick(power_mix, case, "power_mix")
        overrides, provenance = _resolve_modes(doc.get("modes", {}), case)
        return cls(
            name=doc.get("name", path.stem),
            case=case,
            power_mix=power_mix,
            overrides=overrides,
            description=doc.get("description", ""),
            provenance_records=provenance,
        )

    def parameters(self, slug):
        """Default parameters of a mode under this scenario."""
        return mode(slug).replace(**self.overrides.get(slug, {}))

    def provenance(self):
        """DataFrame of every override: mode, parameter, value and evidence."""
        import pandas as pd

        columns = ["mode", "parameter", "case", "value", *PROVENANCE_KEYS]
        rows = [
            [slug, name, self.case, value]
            + [self.provenance_records[slug][name].get(k) for k in PROVENANCE_KEYS]
            for slug, params in sorted(self.overrides.items())
            for name, value in params.items()
        ]
        return pd.DataFrame(rows, columns=columns)


def _locate(path):
    path = pathlib.Path(path)
    if path.exists():
        return path
    packaged = PACKAGED_DIR / f"{path}.toml"
    if path.parent == pathlib.Path(".") and packaged.exists():
        return packaged
    raise FileNotFoundError(
        f"no scenario file '{path}'; packaged scenarios: "
        f"{', '.join(sorted(list_scenarios()))}"
    )


def list_scenarios():
    """Return {name: description} of the packaged scenarios."""
    out = {}
    for file in sorted(PACKAGED_DIR.glob("*.toml")):
        with open(file, "rb") as f:
            out[file.stem] = tomllib.load(f).get("description", "")
    return out
