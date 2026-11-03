"""Validate citation identity, source membership, and literal evidence offsets."""
import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    'repo', nargs='?', type=Path, default=root.parents[2],
    help='repository root (default: inferred from this script location)',
)
parser.add_argument(
    '--labels', type=Path,
    help='explicit released label file; relative paths use the current working directory',
)
parser.add_argument(
    '--split', choices=['dev', 'test', 'all'],
    help='expected split (default: dev, or the explicit label file’s declared split)',
)
args = parser.parse_args()
pre = json.loads((root / 'preregistered_sample.json').read_text())
split = args.split or 'dev'
label_file = args.labels or root / ('evaluation_labels.json' if split == 'all' else f'{split}_labels.json')
if not label_file.is_file():
    parser.error(f'label file does not exist: {label_file}')
labels = json.loads(label_file.read_text())
declared_split = labels.get('split')
if declared_split is not None:
    if declared_split not in {'dev', 'test', 'all'}:
        parser.error(f'unsupported split declared in label file: {declared_split}')
    if args.split is not None and args.split != declared_split:
        parser.error(f'--split {args.split} conflicts with label file split {declared_split}')
    split = declared_split
source_bytes = (args.repo / 'vlb/source/emerson_vlb.txt').read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == pre['source_sha256']
source = source_bytes.decode()
dictionary_gzip = (args.repo / 'docs/dict-conjugated.json.gz').read_bytes()
assert hashlib.sha256(dictionary_gzip).hexdigest() == pre['dictionary_sha256']
dictionary_bytes = gzip.decompress(dictionary_gzip)
dictionary = json.loads(dictionary_bytes)
expected = {c['case_id']: c for c in pre['selected'] if split == 'all' or c['split'] == split}
assert len(labels['cases']) == len(expected)
assert {c['case_id'] for c in labels['cases']} == set(expected)
for c in labels['cases']:
    registered = expected[c['case_id']]
    for key in ['citation_id', 'page_id', 'headword', 'entry_index', 'homonym']:
        assert c[key] == registered[key], (c['case_id'], key)
    assert dictionary[c['entry_index']]['f'] == c['headword']
    page = json.loads(gzip.decompress((args.repo / f"vlb/data/pages/{c['page_id']}.json.gz").read_bytes()))
    assert any(x['id'] == c['citation_id'] for x in page['citations'])
    fragments = {f['id']: f for f in page['fragments']}
    assert c['source_ids'] == list(dict.fromkeys(t['source_id'] for t in c['targets']))
    assert c['status'] != 'clear' or len(c['source_ids']) == 1
    assert c['status'] != 'not_found' or not c['targets']
    for t in c['targets']:
        fragment = fragments[t['source_id']]
        assert t['source_line'] == fragment['source_line']
        assert source[t['form_start0']:t['form_end0']] == t['form']
        assert fragment['text'][t['fragment_start0']:t['fragment_end0']] == t['form']
        assert fragment['source_start0'] + t['fragment_start0'] == t['form_start0']
print(json.dumps({'split': split, 'cases': len(labels['cases']), 'status': dict(Counter(c['status'] for c in labels['cases'])), 'fixture_sha256': hashlib.sha256(label_file.read_bytes()).hexdigest()}, indent=2))
