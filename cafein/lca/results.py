"""Result container: life-cycle components per pkm, vkm and vehicle."""

import math

import pandas as pd

COMPONENTS = ["manufacturing", "delivery", "use", "services", "infrastructure"]

COMPONENT_LABELS = {
    "manufacturing": "Vehicle and battery manufacturing, assembly and "
    "disposal (incl. fluids)",
    "delivery": "Vehicle delivery at point of purchase",
    "use": "Vehicle use (including fuel production)",
    "services": "Operational services",
    "infrastructure": "Infrastructure network",
}


class Result:
    """Energy and GHG results for one mode calculation.

    Components follow the workbook's five life-cycle stages. Per-vehicle
    values have no infrastructure component (the workbook defines
    infrastructure per vkm only), so the per-vehicle total is NaN — exactly
    like the ``#N/A`` in ``0_Total``.
    """

    def __init__(self, params, energy, ghg, coefficient_set=None):
        #: The parameter object used for the calculation.
        self.parameters = params
        #: Name of the coefficient set the session used (e.g. ``itf-2020``).
        self.coefficient_set = coefficient_set
        self._frames = {"energy": energy, "ghg": ghg}

    def _series(self, metric, per):
        values = self._frames[metric][per]
        s = pd.Series(values, index=COMPONENTS, name=f"{metric}_{per}")
        s["total"] = values.sum() if per != "vehicle" else math.nan
        return s

    @property
    def per_pkm(self):
        """GHG emissions per pkm by component [g CO2-eq/pkm]."""
        return self._series("ghg", "pkm")

    @property
    def energy_per_pkm(self):
        """Energy use per pkm by component [MJ/pkm]."""
        return self._series("energy", "pkm")

    @property
    def per_vkm(self):
        """GHG emissions per vkm by component [g CO2-eq/vkm]."""
        return self._series("ghg", "vkm")

    @property
    def energy_per_vkm(self):
        """Energy use per vkm by component [MJ/vkm]."""
        return self._series("energy", "vkm")

    @property
    def ghg_per_pkm(self):
        """Total GHG emissions [g CO2-eq/pkm]."""
        return float(self.per_pkm["total"])

    @property
    def energy_per_pkm_total(self):
        """Total energy use [MJ/pkm]."""
        return float(self.energy_per_pkm["total"])

    def to_frame(self):
        """Tidy DataFrame: component x (metric, per) with totals."""
        columns = {}
        for metric in ("energy", "ghg"):
            for per in ("pkm", "vkm", "vehicle"):
                columns[(metric, per)] = self._series(metric, per)
        frame = pd.DataFrame(columns)
        frame.columns = pd.MultiIndex.from_tuples(
            frame.columns, names=["metric", "per"]
        )
        return frame

    def __repr__(self):
        return (
            f"<Result {self.parameters.slug}: "
            f"{self.ghg_per_pkm:.1f} g CO2-eq/pkm, "
            f"{self.energy_per_pkm_total:.2f} MJ/pkm>"
        )
