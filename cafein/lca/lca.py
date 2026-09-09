"""Public entry point: the TransportLCA session object."""

import math

import numpy as np

from . import modes as modes_registry
from .config import (
    DEFAULT_COEFFICIENTS,
    POWER_SOURCES,
    available_coefficient_sets,
    conf,
)
from .engine import delivery, infrastructure, manufacturing, services, use
from .parameters import ModeParameters
from .results import Result

_MIX_SUM_TOLERANCE = 1e-6


class TransportLCA:
    """Life-cycle assessment session with shared environment assumptions.

    Parameters
    ----------
    power_mix : str or dict, optional
        Electricity generation mix used by every calculation whose mode does
        not pin an explicit ``electricity_region``. Either the name of a
        packaged region preset (see ``conf.power_mix_catalog``) or a custom
        mapping of the six generation sources (oil, natural_gas, coal,
        nuclear, biomass, other_renewables) to shares summing to 1. Defaults
        to the scenario's mix, else "World".
    scenario : Scenario, optional
        Parameter overrides applied to every mode given by slug (see
        :class:`~cafein.lca.Scenario`); keyword overrides on
        :meth:`calculate` still win.
    coefficients : str, optional
        Name of the packaged coefficient set (see
        ``cafein.lca.available_coefficient_sets``). Resolved as this argument,
        else the scenario's ``coefficients`` key, else the default
        ``"itf-2020"``; an unknown name raises ``KeyError``. 0.1.0 ships one
        set, so this selects the default and records provenance.
    """

    def __init__(self, power_mix=None, scenario=None, coefficients=None):
        self.scenario = scenario
        if coefficients is None:
            coefficients = (
                getattr(scenario, "coefficients", None) or DEFAULT_COEFFICIENTS
            )
        available = available_coefficient_sets()
        if coefficients not in available:
            raise KeyError(
                f"unknown coefficient set '{coefficients}'. Available: "
                f"{', '.join(available)}"
            )
        #: The coefficient set backing this session. 0.1.0 ships one set
        #: (``itf-2020``); the module-level ``conf`` reads from it, so a
        #: process uses a single set at a time.
        self.coefficients = coefficients
        if power_mix is None:
            power_mix = getattr(scenario, "power_mix", None) or "World"
        if isinstance(power_mix, dict):
            self._default_mix = self._validate_mix(power_mix)
            self.power_mix = "custom"
        else:
            if power_mix not in conf.power_mix_catalog:
                raise KeyError(
                    f"unknown power mix region '{power_mix}'. Available: "
                    f"{', '.join(sorted(conf.power_mix_catalog))}"
                )
            self._default_mix = conf.power_mix_catalog[power_mix]
            self.power_mix = power_mix

    @staticmethod
    def _validate_mix(mix):
        unknown = set(mix) - set(POWER_SOURCES)
        if unknown:
            raise KeyError(
                f"unknown generation source(s): {', '.join(sorted(unknown))}."
                f" Valid sources: {', '.join(POWER_SOURCES)}"
            )
        shares = [float(mix.get(s, 0.0)) for s in POWER_SOURCES]
        if abs(sum(shares) - 1) > _MIX_SUM_TOLERANCE:
            raise ValueError(
                f"generation mix shares must sum to 1, got {sum(shares):.6f}"
            )
        return shares

    def _mix_for(self, params):
        """Session/mode electricity-mix precedence (plan section 7)."""
        if params.electricity_region is None:
            return self._default_mix
        return conf.power_mix_catalog[params.electricity_region]

    def parameters(self, slug):
        """Default parameters of a mode under the session scenario."""
        if self.scenario is None:
            return modes_registry.mode(slug)
        return self.scenario.parameters(slug)

    def calculate(self, mode, **overrides):
        """Calculate life-cycle energy and GHG for a mode.

        ``mode`` is a mode slug (see :func:`cafein.lca.list_modes`), to which
        the session scenario applies, or a
        :class:`~cafein.lca.parameters.ModeParameters` object used as given;
        keyword overrides are applied last with ``.replace()``.
        """
        if isinstance(mode, str):
            params = self.parameters(mode)
        elif isinstance(mode, ModeParameters):
            params = mode
        else:
            raise TypeError(
                "mode must be a slug string or ModeParameters, got "
                f"{type(mode).__name__}"
            )
        if overrides:
            params = params.replace(**overrides)
        data = modes_registry._data_for(params)
        mix = self._mix_for(params)

        # Stage results (per vehicle; infrastructure per vkm).
        battery_weight = manufacturing.battery_weight_kg(params)
        mfg_e, mfg_g = manufacturing.run(params, data)
        del_e, del_g = delivery.run(params, data, battery_weight)
        use_e, use_g = use.run(params, mix)
        # Servicing vehicles run on the session default mix (the workbook
        # derives their intensities from its default-region column).
        ref_use_energy = ref_annual_km = None
        if data.services_ref_column:
            ref_params, _ = modes_registry._mode_by_column(data.services_ref_column)
            ref_use_energy, _ = use.run(ref_params, self._mix_for(ref_params))
            ref_annual_km = ref_params.annual_km
        srv_e, srv_g = services.run(
            params, data, use_e, use_g, self._default_mix, ref_use_energy, ref_annual_km
        )
        inf_e_vkm, inf_g_vkm = infrastructure.run(params, data)

        # 0_Total R17/R22: deadheading of self-serviced fleets stretches the
        # lifetime mileage with zero-occupancy km.
        lifetime_km = params.lifetime_km  # R7
        deadhead_km = 0.0
        if params.service_vehicle == params.name:  # R19 == R2
            deadhead_km = (
                params.service_km_per_vehicle_day * 365 * params.lifetime_years
            )
        lifetime_km_total = lifetime_km + deadhead_km  # R22
        occupancy_effective = params.occupancy * lifetime_km / lifetime_km_total  # R17

        per_vehicle = np.array([mfg_e, del_e, use_e, srv_e, math.nan]), np.array(
            [mfg_g, del_g, use_g, srv_g, math.nan]
        )
        energy, ghg = {}, {}
        energy["vehicle"], ghg["vehicle"] = per_vehicle
        energy["vkm"] = np.append(energy["vehicle"][:4] / lifetime_km_total, inf_e_vkm)
        ghg["vkm"] = np.append(ghg["vehicle"][:4] / lifetime_km_total, inf_g_vkm)
        energy["pkm"] = energy["vkm"] / occupancy_effective
        ghg["pkm"] = ghg["vkm"] / occupancy_effective
        return Result(params, energy, ghg, coefficient_set=self.coefficients)

    def summary(self, per="pkm", metric="ghg"):
        """DataFrame of all canonical modes x components (like the report
        tables)."""
        import pandas as pd

        rows = {}
        for slug in modes_registry.CANONICAL_MODES:
            result = self.calculate(slug)
            series = result._series(metric, per)
            rows[slug] = series
        return pd.DataFrame(rows).T

    def transit_factors(self, modes=None, identities=None):
        """cafein-ready transit factor table (see ``cafein.lca.export``)."""
        from . import export

        return export.transit_factors(self, modes=modes, identities=identities)

    def street_factors(self, modes=None, identities=None):
        """cafein-ready street factor table (see ``cafein.lca.export``)."""
        from . import export

        return export.street_factors(self, modes=modes, identities=identities)
