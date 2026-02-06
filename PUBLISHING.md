# Publishing Guide

This repo is designed to be small and easy to audit. Typical release flow:

## 1) Prepare a release

- Update version in `firefinder/__init__.py` and `pyproject.toml`.
- Run tests: `python -m pytest`.
- Update `README.md` if behavior or API changed.

## 2) GitHub release

- Commit changes and tag a release (for example `v0.1.0`).
- Push to GitHub and create a release from the tag.

## 3) (Optional) Publish to PyPI

If you want this on PyPI:

- Build: `python -m build` (requires `build` installed)
- Upload: `python -m twine upload dist/*`

You can skip this step if you only want GitHub source releases.
