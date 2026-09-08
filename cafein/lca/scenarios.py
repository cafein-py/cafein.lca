"""Scenario bundles: named sets of per-mode parameter overrides.

A scenario is a TOML document::

    name = "india"
    description = "Indian metropolitan operating conditions"
    power_mix = "India"                 # preset, shares table, or per case

    [modes.bus_ice]
    occupancy = {best = 92, central = 53, worst = 25}
    lifetime_years = 12

    [modes."private_car_*"]             # glob pattern over mode slugs
    occupancy = {best = 1.97, central = 1.25, worst = 1.0}

Every value is either a scalar or a table of the three cases ``best``,
``central`` and ``worst``, named by their effect on emissions per pkm.
``power_mix`` is a packaged preset name, a table of the six generation
shares, or a per-case table of either. Exact slugs take precedence over glob
patterns; patterns apply in file order.
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


def _resolve_modes(table, case):
    exact, patterns = {}, {}
    for key, params in table.items():
        if not isinstance(params, dict):
            raise ValueError(f"[modes.{key}] must be a table of parameters")
        picked = {
            name: _pick(v, case, f"modes.{key}.{name}") for name, v in params.items()
        }
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
    resolved = {}
    for slug in patterns.keys() | exact.keys():
        merged = {**patterns.get(slug, {}), **exact.get(slug, {})}
        mode(slug).replace(**merged)  # validates names and ranges
        resolved[slug] = merged
    return resolved


@dataclasses.dataclass(frozen=True)
class Scenario:
    """A named bundle of parameter overrides and an electricity mix.

    Build one with :meth:`load`; ``overrides`` maps canonical mode slugs to
    the parameter values of the selected ``case``.
    """

    name: str
    case: str = "central"
    power_mix: object = None
    overrides: dict = dataclasses.field(default_factory=dict)
    description: str = ""

    @classmethod
    def load(cls, path, case="central"):
        """Load a scenario TOML file for one of the three cases."""
        if case not in CASES:
            raise ValueError(f"case must be one of {', '.join(CASES)}, got {case!r}")
        with open(pathlib.Path(path), "rb") as f:
            doc = tomllib.load(f)
        unknown = set(doc) - {"name", "description", "power_mix", "modes"}
        if unknown:
            raise ValueError(f"unknown top-level keys: {', '.join(sorted(unknown))}")
        power_mix = doc.get("power_mix")
        if isinstance(power_mix, dict) and set(power_mix) <= set(CASES):
            power_mix = _pick(power_mix, case, "power_mix")
        return cls(
            name=doc.get("name", pathlib.Path(path).stem),
            case=case,
            power_mix=power_mix,
            overrides=_resolve_modes(doc.get("modes", {}), case),
            description=doc.get("description", ""),
        )

    def parameters(self, slug):
        """Default parameters of a mode under this scenario."""
        return mode(slug).replace(**self.overrides.get(slug, {}))
