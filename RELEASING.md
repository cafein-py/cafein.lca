# Releasing

1. Update `CHANGELOG.md`: move the unreleased items under the new version
   heading with the release date.
2. Set the version in `pyproject.toml` and `cafein/lca/__init__.py`
   (`__version__`) — they must match the tag.
3. Commit, push, and wait for CI to go green on the full matrix.
4. Dry run: trigger the *Release* workflow manually (`workflow_dispatch`) —
   it runs tests and builds the sdist/wheel without publishing.
5. Tag and push: `git tag v0.1.0 && git push origin v0.1.0`. The tag-driven
   run tests, checks the tag against the package version, builds, publishes
   to PyPI via Trusted Publishing (OIDC; the `pypi` environment must be
   configured in the repo settings and the project registered as a trusted
   publisher on PyPI), and creates the GitHub release.
6. Post-release: bump to the next `.dev0` version; check the Zenodo record
   (if the GitHub–Zenodo integration is enabled, the release is archived
   automatically using `.zenodo.json`).
7. conda-forge: after the first PyPI release, submit a feedstock to
   conda-forge/staged-recipes.
