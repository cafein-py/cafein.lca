"""cafein.lca: Life-cycle assessment of urban passenger transport in Python.

Adapted from the life-cycle assessment model published with Cazzola & Crist
(2020), "Good to Go? Assessing the Environmental Performance of New
Mobility", International Transport Forum, Paris.
"""

from .config import available_coefficient_sets
from .lca import TransportLCA
from .modes import list_modes, mode
from .scenarios import Scenario, list_scenarios

__version__ = "0.1.0"

__all__ = [
    "TransportLCA",
    "Scenario",
    "list_scenarios",
    "available_coefficient_sets",
    "mode",
    "list_modes",
    "__version__",
]
