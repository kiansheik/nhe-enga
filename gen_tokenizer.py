import json

with open('docs/dict-conjugated.json', 'r') as f:
    data = json.load(f)

conjugations = [x for x in data if 'c' in x.keys()]

len(conjugations[0])