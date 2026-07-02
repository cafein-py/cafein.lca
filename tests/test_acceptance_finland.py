"""Acceptance test: reproduce the repo's Finland-2020 gCO2/pkm table.

``gCO2-per-pkm-by-transport-mode.csv`` was produced from the workbook with
its World electricity column replaced by Finland 2020 generation data. The
same numbers must fall out of a TransportLCA session with the equivalent
custom power mix — the worked example of plan section 7.
"""

import csv
import pathlib

import pytest

from cafein_lca import TransportLCA

CSV = pathlib.Path(__file__).parent.parent / "gCO2-per-pkm-by-transport-mode.csv"

FINLAND_2020 = {
    "oil": 0.0038726960370381153,
    "natural_gas": 0.05389744635005678,
    "coal": 0.07991439303497073,
    "nuclear": 0.33909384736336373,
    "biomass": 0.16009084820778616,
    "other_renewables": 0.3631307690067845,
}

#: CSV column header -> mode slug, in file order.
CSV_MODES = {
    "Private e-scooter": "private_escooter",
    "Shared e-scooter (1st gen.)": "shared_escooter_first_gen",
    "Shared e-scooter (new gen.)": "shared_escooter_new_gen",
    "Private bike": "private_bike",
    "Shared bike": "shared_bike",
    "Private e-bike": "private_ebike",
    "Shared e-bike": "shared_ebike",
    "Private moped - ICE": "private_moped_ice",
    "Private moped - BEV": "private_moped_bev",
    "Shared moped - ICE": "shared_moped_ice",
    "Shared moped - BEV": "shared_moped_bev",
    "Private car - ICE": "private_car_ice",
    "Private car - HEV": "private_car_hev",
    "Private car - PHEV": "private_car_phev",
    "Private car - BEV": "private_car_bev",
    "Private car - FCEV": "private_car_fcev",
    "Taxi - HEV": "taxi_hev",
    "Taxi - BEV": "taxi_bev",
    "Taxi - BEV (two packs)": "taxi_bev_two_packs",
    "Taxi - FCEV": "taxi_fcev",
    "Ridesourcing - car - ICE": "ridesourcing_car_ice",
    "Ridesourcing - car - HEV": "ridesourcing_car_hev",
    "Ridesourcing - car - PHEV": "ridesourcing_car_phev",
    "Ridesourcing - car - BEV": "ridesourcing_car_bev",
    "Ridesourcing - car - BEV (two packs)":
        "ridesourcing_car_bev_two_packs",
    "Ridesourcing - car - FCEV": "ridesourcing_car_fcev",
    "Bus - ICE": "bus_ice",
    "Bus - HEV": "bus_hev",
    "Bus - BEV": "bus_bev",
    "Bus - BEV (two packs)": "bus_bev_two_packs",
    "Bus - FCEV": "bus_fcev",
    "Metro/urban train": "metro_urban_train",
}

#: CSV row label -> result components summed into it.
CSV_COMPONENTS = {
    "Vehicle component": ("manufacturing", "delivery"),
    "Fuel component": ("use",),
    "Infrastructure componen": ("infrastructure",),
    "Operational services": ("services",),
}

#: The report figures (and hence the CSV) move the deadheading share of the
#: use-phase burden into "Operational services" for taxi and ridesourcing
#: modes (Figure sheets row 60 = Tech_Spec_TNC!P14).
DEADHEADING_SHARE = 0.38588235294117645
DEADHEADING_MODES = frozenset(
    slug for slug in CSV_MODES.values()
    if slug.startswith(("taxi_", "ridesourcing_"))
)


def _read_reference():
    with open(CSV, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    header = rows[0][1:]
    table = {}
    for row in rows[1:]:
        label = row[0]
        for name, value in zip(header, row[1:]):
            table.setdefault(name, {})[label] = float(value)
    return table


@pytest.mark.parametrize("csv_name,slug", CSV_MODES.items(),
                         ids=CSV_MODES.values())
def test_finland_mix_reproduces_repo_csv(csv_name, slug):
    lca = TransportLCA(power_mix=FINLAND_2020)
    reference = _read_reference()[csv_name]
    per_pkm = lca.calculate(slug).per_pkm
    for label, components in CSV_COMPONENTS.items():
        ours = sum(per_pkm[c] for c in components)
        if slug in DEADHEADING_MODES:
            if label == "Fuel component":
                ours *= 1 - DEADHEADING_SHARE
            elif label == "Operational services":
                ours += per_pkm["use"] * DEADHEADING_SHARE
        # The reference table holds values rounded to integers.
        assert abs(ours - reference[label]) <= 0.5 + 1e-9, (
            f"{slug} {label}: computed {ours:.3f}, reference "
            f"{reference[label]}")
