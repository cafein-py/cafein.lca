"""cafein-lca: the ITF "Good to go?" urban transport LCA model in Python.

Reimplements the life-cycle assessment workbook published with Cazzola &
Crist (2020), "Good to Go? Assessing the Environmental Performance of New
Mobility", International Transport Forum, Paris.
"""

from .lca import TransportLCA
from .modes import list_modes, mode

__version__ = "0.1.0.dev0"

__all__ = ["TransportLCA", "mode", "list_modes", "__version__"]
