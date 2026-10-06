# Data scripts

Maintained, repository-specific pipelines for rebuilding published datasets and primary-source derivatives.

Run these scripts from the repository root because their input and output paths are intentionally relative to the checkout. Prefer the documented Make targets when one exists:

- `make gen_data` runs `gen_data.py` and `verbs.py`, then refreshes Pydicate's bundled conjugation data.
- `nheengatu_dict_miner.py` and `nheengatu_pluriforme_fix.py` rebuild the Nheengatu dictionary artifacts.
- `mbya_dooley_miner.py` rebuilds the Mbyá dictionary artifacts.
- `source_extraction.py` rebuilds citation counters and derived page images.
- `python scripts/data/source_inventory.py` audits the **served** `docs/dict-conjugated.json.gz` against Navarro's bibliography and the current `linkSources()` formatter. It writes [the source queue](../../docs/primary_sources/source_inventory.md), machine-readable inventory, complete compressed citation audit, and D'Evreux citation CSV under `docs/primary_sources/`. It needs Python's standard library and Node.js, changes no dictionary data, and renders no images. Use `--output-dir /tmp/source-inventory` for a reproducibility comparison.

## Next-source groundwork

The [local-agent plans](../../docs/primary_sources/plans/README.md) pin the
Figueira, Castilho, Sousa, and D’Abbeville PDFs and distinguish checked targets
from pending mappings. These research JSON files are not renderer manifests.
Adapt the existing renderer/viewer as described there before generating assets.

`python3 scripts/check_pages_size.py .pages-build` measures the complete
optimized site against a 900 MB project budget (a buffer below Pages’ 1 GB
limit). It is read-only and also accepts `--tree-json` for a complete GitHub
Git Trees response. The focused checks run with:

```bash
python3 -m unittest discover -s tests -p test_pages_size.py -v
```
