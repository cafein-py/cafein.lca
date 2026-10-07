"""cafein.lca: Life-cycle assessment of urban passenger transport in Python.

Adapted from the life-cycle assessment model published with Cazzola & Crist
(2020), "Good to Go? Assessing the Environmental Performance of New
Mobility", International Transport Forum, Paris.
"""

from .config import available_coefficient_sets
from .export import gtfs_identities
from .lca import TransportLCA
from .modes import list_modes, mode, mode_provenance
from .scenarios import Scenario, list_scenarios

__version__ = "0.2.0.dev0"

__all__ = [
    "TransportLCA",
    "Scenario",
    "list_scenarios",
    "available_coefficient_sets",
    "gtfs_identities",
    "mode",
    "list_modes",
    "mode_provenance",
    "__version__",
]
