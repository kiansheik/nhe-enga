# Data scripts

Maintained, repository-specific pipelines for rebuilding published datasets and primary-source derivatives.

Run these scripts from the repository root because their input and output paths are intentionally relative to the checkout. Prefer the documented Make targets when one exists:

- `make gen_data` runs `gen_data.py` and `verbs.py`, then refreshes Pydicate's bundled conjugation data.
- `nheengatu_dict_miner.py` and `nheengatu_pluriforme_fix.py` rebuild the Nheengatu dictionary artifacts.
- `mbya_dooley_miner.py` rebuilds the Mbyá dictionary artifacts.
- `source_extraction.py` rebuilds citation counters and derived page images.
