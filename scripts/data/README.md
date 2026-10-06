# Data scripts

Maintained, repository-specific pipelines for rebuilding published datasets and primary-source derivatives.

Run these scripts from the repository root because their input and output paths are intentionally relative to the checkout. Prefer the documented Make targets when one exists:

- `make gen_data` runs `gen_data.py` and `verbs.py`, then refreshes Pydicate's bundled conjugation data.
- `nheengatu_dict_miner.py` and `nheengatu_pluriforme_fix.py` rebuild the Nheengatu dictionary artifacts.
- `mbya_dooley_miner.py` rebuilds the Mbyá dictionary artifacts.
- `source_extraction.py` rebuilds citation counters and derived page images.
- `python scripts/data/source_inventory.py` audits the **served** `docs/dict-conjugated.json.gz` against Navarro's bibliography and the current `linkSources()` formatter. It writes [the source queue](../../docs/primary_sources/source_inventory.md), machine-readable inventory, complete compressed citation audit, and D'Evreux citation CSV under `docs/primary_sources/`. It needs Python's standard library and Node.js, changes no dictionary data, and renders no images. Use `--output-dir /tmp/source-inventory` for a reproducibility comparison.
