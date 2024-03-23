#!/usr/bin/env python -i
import json
from collections import Counter
from itertools import product
import random
from tqdm import tqdm
import matplotlib.pyplot as plt
import sys
sys.path.append('tupi')
from tupi import Noun, Verb, TupiAntigo
import unicodedata

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

with open("docs/tupi_dict_navarro.js", "r") as file:
    lines = file.readlines()
    lines[0] = lines[0][lines[0].find("=") + 1 : -2]

ban = [
    "NOTA",
    "Daí",
    "De",
    "OBSERVAÇÃO",
    "Daí,",
    "aba",
    "-ab",
    "abatiputá",
    "-agûama",
    "a'ebé",
    "agûaîxima",
    "agûaragûasu",
    "agûy",
    "ambûer",
    "apyrĩ",
    "ambype",
    "gûaîá",
    "eno-",
    "îabotimirĩ",
    "îapĩ",
    "Maíra",
    "memetipó",
    "moro-",
    "muresi",
    "pyru'ã",
    "POROROCA",
    "sybyamumbyaré",
    "Muitos",
    "Há",
    "O",
    "Cardim,",
]
# Parse the JSON data into a Python object
dicc = json.loads(lines[0])
dicc_dict = {i: v for i, v in enumerate(dicc)}
tupi_only = []
include = False
adjectives = []
for i, vbt in dicc_dict.items():
    if vbt["first_word"] == "ã":
        include = True
    if include and vbt["first_word"] not in ban and "adj.: " not in vbt["definition"]:
        vbt["id"] = i
        tupi_only.append(vbt)
    if vbt["first_word"] == "'yura":
        include = False

adj_raws = [
    (
        x["first_word"].replace("(e)", "e").replace("teînhẽa", "tenhẽa"),
        x["definition"]
        .split("adj.: ")[1]
        .split(") ")[0]
        .split("):")[0]
        .split(" ")[0]
        .replace(",", "")
        .replace("(e)", "e")
        .replace("ygapenung", "yapenung"),
        x["optional_number"],
        x["definition"],
        i,
    )
    for i, x in dicc_dict.items()
    if "adj.: " in x["definition"]
]
for first_word, optional_number, definition, vid in {
    (x[1], x[2], x[3], x[4]) for x in adj_raws
}:
    tupi_only.append(
        {
            "first_word": first_word,
            "optional_number": optional_number,
            "definition": "adj. " + definition,
            "id": vid,
        }
    )

noun_types = [
    "(t)",
    "(t, t)",
    "(r, s)",
    "(s, r, s)",
]
count = Counter()
noun_types = sorted(noun_types, key=len, reverse=True)
nouns = {vt: [] for vt in noun_types + ["other"]}
all_verbetes = []
all_nouns = set()
possible_letters = set()
for vbt in tupi_only:
    for vclass in [
        "(s.)",
            "(s. - portug.)",
        "(s) (v.tr.)",
        "(v.tr.)",
        "(v. intr.)",
        "(v. da 2ª classe)",
        "(-îo-, -s-) (v.tr. irreg. Incorpora -îo- (ou -nho-) e -s- no indicativo e formas derivadas deste.)",
        "(xe) (r, s) (v. da 2ª classe)",
        "(r, s) (xe) (v. da 2ª classe)",
        "(-îo-) (v.tr.)",
        "(-îo- ou -nho-) (v.tr.)",
        "(-îo-s- ou -nho-s-) (v.tr. irreg. Incorpora -îo- e -s-. Nas formas nominais é pluriforme.)",
        "adj.: "
    ]:
        if vclass in vbt["definition"]:
            found = False
            for vt in noun_types:
                if vt in vbt["definition"][:50]:
                    word = vbt["first_word"].strip().replace("-", "")
                    nouns[vt].append(vbt)
                    all_nouns.add(word)
                    all_verbetes.append(vbt)
                    for letter in word:
                        possible_letters.add(letter)
                    count.update([vt])
                    found = True
                    break
            if not found:
                vt = "other"
                word = vbt["first_word"].strip().replace("-", "")
                nouns[vt].append(vbt)
                all_nouns.add(word)
                all_verbetes.append(vbt)
                for letter in word:
                    possible_letters.add(letter)
                count.update([vt])

all_nouns = sorted(list(all_nouns))
all_nouns_objs = [Noun(x['first_word'], x['definition']) for x in all_verbetes]
possible_letters = sorted(possible_letters)


breakpoint()

# Extract data for histogram
values, frequencies = zip(*sorted(count.items(), key=lambda x: x[1], reverse=True))

for i in range(len(values)):
    print(f"{values[i]}:\t{frequencies[i]}")
# Plot histogram
# plt.bar(values, frequencies, color='blue', alpha=0.7)
# plt.xlabel('Values')
# plt.ylabel('Frequencies')
# plt.title('Histogram based on Counter object')
# # Rotate x-axis labels by 90 degrees
# plt.xticks(rotation=-90)
# # Set logarithmic scale on the y-axis
# plt.yscale('log')
# plt.show()
random.shuffle(all_nouns_objs)
# for noun in all_nouns_objs[:len(all_nouns_objs)//2]:
#     print(noun, f"({noun.pluriforme})", noun.raw_definition[:50])
#     print(noun.sara(), "\t\t", noun.sara().substantivo(anotated=True))
#     print(noun.saba(), "\t\t", noun.saba().substantivo(anotated=True))
#     print(noun.possessive("1ps"), "\t\t", noun.possessive("1ps").substantivo(anotated=True))
#     print(noun.possessive("3p"), "\t\t", noun.possessive("3p").substantivo(anotated=True))
#     print(noun.absoluta(), "\t\t", noun.absoluta().substantivo(anotated=True))
#     print()
results = []
persons = [
        "1ps",
        "1ppi",
        "1ppe",
        "2ps",
        "2pp",
        "3p",
        "absoluta"
    ]
# write each x.verbete() for x in all_nouns_objs to a json list
with open('docs/all_nouns_verbs.json', 'w') as f:
    # use json to write to file
    json.dump(list({x.verbete() for x in all_nouns_objs}), f)
for noun in tqdm(all_nouns_objs):
    for person in persons:
        n = noun
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.ram()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.ram().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))


        n = noun.saba()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.saba().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.saba().ram()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.saba().ram().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))


        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.sara()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.sara().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.sara().ram()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.sara().ram().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))



        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.pyr()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.pyr().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.pyr().ram()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.pyr().ram().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))

        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.emi()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.emi().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.emi().ram()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.emi().ram().puer()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))


        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.bae()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.puer().bae()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.ram().bae()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))
        n = noun.ram().puer().bae()
        n = n.possessive(person)
        results.append((n.substantivo(anotated=False),n.recreate_annotated()))

def introduce_typo(s):
    typo_type = random.choice(['swap', 'add', 'remove'])
    if typo_type == 'swap' and len(s) > 1:
        pos = random.randint(0, len(s) - 2)
        s = s[:pos] + s[pos+1] + s[pos] + s[pos+2:]
    elif typo_type == 'add':
        pos = random.randint(0, len(s))
        char = random.choice("p pû pî b t s sû k kû ' m mû n r nh ng mb mbû nd ndû ng ngû gû g û î ŷ a á e é i í y ý o ó u ú ã ẽ ĩ ỹ õ ũ x".split(" "))
        s = s[:pos] + char + s[pos:]
    elif typo_type == 'remove' and len(s) > 1:
        pos = random.randint(0, len(s) - 1)
        s = s[:pos] + s[pos+1:]
    return s

# Example usage
original_string = "hello world"
typo_string = introduce_typo(original_string)
print(typo_string)


import json, re
uniq_results = set(results)
results = []
# Augment the data for more robust results
t = TupiAntigo()
for src, recreate in tqdm(uniq_results):
    for aug_func in [strip_accents, lambda x:x, introduce_typo, t.fix_phonetics]:
        results.append((aug_func(src), recreate))
# Write results to file
results = [{"anotated":x[1], "label":x[0]} for x in set(results)]
with open('anotated_results_nouns.json', 'w') as f:
    # use json to write to file
    json.dump(results, f)

def tokenize_string(annotated_string):
    matches = re.findall(r'([^\s\[\]]+)?(\[.*?\])', annotated_string)
    notes = {(token, annotation) for token, annotation in matches}
    for tag in {(None, annotation) for _, annotation in matches}:
        notes.add(tag)
    return notes

print("test")
from collections import Counter
c = Counter()
for res in results:
    c.update(tokenize_string(res['anotated']))
for mc in c.most_common(25):
    print(mc)

# Write the .keys contents of c to a file as a json list
with open('anotated_tokens_nouns.json', 'w') as f:
    # use json to write to file
    json.dump(list(set([y for x in c.keys() for y in x if y and '[' in y])), f)