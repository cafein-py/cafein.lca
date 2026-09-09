API reference
=============

Session
-------

A ``TransportLCA`` holds the session assumptions and runs calculations.

.. autosummary::
   :toctree: generated/

   cafein.lca.TransportLCA
   cafein.lca.TransportLCA.calculate
   cafein.lca.TransportLCA.summary
   cafein.lca.TransportLCA.parameters
   cafein.lca.TransportLCA.transit_factors
   cafein.lca.TransportLCA.street_factors

Modes and parameters
--------------------

.. autosummary::
   :toctree: generated/

   cafein.lca.list_modes
   cafein.lca.mode
   cafein.lca.parameters.ModeParameters
   cafein.lca.parameters.ModeParameters.replace
   cafein.lca.parameters.ModeParameters.lifetime_km

Results
-------

.. autosummary::
   :toctree: generated/

   cafein.lca.results.Result
   cafein.lca.results.Result.per_pkm
   cafein.lca.results.Result.per_vkm
   cafein.lca.results.Result.energy_per_pkm
   cafein.lca.results.Result.energy_per_vkm
   cafein.lca.results.Result.ghg_per_pkm
   cafein.lca.results.Result.energy_per_pkm_total
   cafein.lca.results.Result.to_frame

Scenarios
---------

.. autosummary::
   :toctree: generated/

   cafein.lca.list_scenarios
   cafein.lca.Scenario
   cafein.lca.Scenario.load
   cafein.lca.Scenario.parameters
   cafein.lca.Scenario.provenance
