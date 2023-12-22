import json
from collections import Counter
from itertools import product
from tqdm import tqdm
import matplotlib.pyplot as plt
import tupi

with open("../docs/tupi_dict_navarro.js", "r") as file:
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
tupi_only = []
include = False
adjectives = []
for vbt in dicc:
    if vbt["first_word"] == "ã":
        include = True
    if include and vbt["first_word"] not in ban and "adj.: " not in vbt["definition"]:
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
    )
    for x in dicc
    if "adj.: " in x["definition"]
]
for first_word, optional_number, definition in {(x[1], x[2], x[3]) for x in adj_raws}:
    tupi_only.append(
        {
            "first_word": first_word,
            "optional_number": optional_number,
            "definition": definition,
        }
    )

verb_types = [
    "(s) (v.tr.)",
    "(v.tr. irreg.; no indicativo é usado somente com objeto incorporado)",
    "(v.tr.)",
    "(v. intr.)",
    "(v. da 2ª classe)",
    "(v. intr. compl. posp.)",
    "(v. intr. irreg., usado no imper. somente)",
    "(v.tr. ou intr.)",
    "(s) (v.tr. e intr.)",
    "2ª p. do sing. irreg. do imper. d",
    "(-îo-, -s-) (v.tr. irreg. Incorpora -îo- (ou -nho-) e -s- no indicativo e formas derivadas deste.)",
    "(xe) (r, s) (v. da 2ª classe)",
    "(v. irreg. - forma só usada no imper.)",
    "(v.tr.) (Pode ter gerúndio irregular",
    "ger. irreg. d",
    "2ª p. irreg. do imper. d",
    "forma do gerúndio d",
    "1ª p. do sing. do gerúndio d",
    "(v. tr. irreg.)",
    "(v. intr. irreg.)",
    "(v. intr. irreg. usado somente no plural)",
    "(t) (v. intr. compl. posp. irreg.)",
    "ger. d",
    "(-îo-) (v.tr.)",
    "(-îo- ou -nho-) (v.tr.)",
    "(v. tr. compl. posp.)",
    "3ª p. do indic. d",
    "3ª p. do gerúndio d",
    "2ª p. irreg. do pl. d",
    "forma do modo indicativo circunstancial d",
    "gerúndio d",
    "(v. irreg. Só usado com objeto incorporado nas formas verbais propriamente ditas. Nas formas nominais, comporta-se como qualquer outro verbo regular.)",
    "forma de 3ª p. do modo indicativo circunstancial d",
    "forma irreg. d",
    "(v.tr. irreg. - não recebe o pronome -î- incorporado)",
    "(-îo-s- ou -nho-s-) (v.tr. irreg. Incorpora -îo- e -s-. Nas formas nominais é pluriforme.)",
]
count = Counter()
verb_types = ["adj.: "] + sorted(verb_types, key=len, reverse=True)
verbs = {vt: [] for vt in verb_types + ["other"]}
all_verbetes = []
all_verbs = set()
possible_letters = set()
for vbt in tupi_only:
    if "adj.: " in vbt["definition"] or (
        "(v." in vbt["definition"]
        and "(s.)" not in vbt["definition"]
        and "o mesmo que" not in vbt["definition"]
        and "alomorfe" not in vbt["definition"]
        and "contração d" not in vbt["definition"]
        and "nasalização d" not in vbt["definition"]
        and "forma nasalizada d" not in vbt["definition"]
        and "forma nasal. d" not in vbt["definition"]
        and "variante d" not in vbt["definition"]
        and "forma negativa d" not in vbt["definition"]
        and "metátese d" not in vbt["definition"]
        and "forma absol. d" not in vbt["definition"]
        and "forma absoluta d" not in vbt["definition"]
    ):
        found = False
        for vt in verb_types:
            if vt in vbt["definition"]:
                if vt == "(v.tr.)" and "(s)" in vbt["definition"][:50]:
                    vt = "(s) (v.tr.)"
                word = vbt["first_word"].strip().replace("-", "")
                verbs[vt].append(vbt)
                all_verbs.add(word)
                all_verbetes.append(vbt)
                for letter in word:
                    possible_letters.add(letter)
                count.update([vt])
                found = True
                break
        if not found:
            verbs["other"].append(vbt)

all_verbs = sorted(list(all_verbs))
possible_letters = sorted(possible_letters)

# print([(k, len(verbs[k])) for k in verbs.keys()])
print()

# Extract data for histogram
values, frequencies = zip(*sorted(count.items(), key=lambda x: x[1], reverse=True))

for i in range(len(values)):
    print(f"{values[i]}:\t{frequencies[i]}")
# # Plot histogram
# plt.bar(values, frequencies, color='blue', alpha=0.7)
# plt.xlabel('Values')
# plt.ylabel('Frequencies')
# plt.title('Histogram based on Counter object')
# # Rotate x-axis labels by 90 degrees
# plt.xticks(rotation=-90)
# # Set logarithmic scale on the y-axis
# plt.yscale('log')
# plt.show()

intr_raiz = {
    "mo" + item["first_word"]
    for sublist in [verbs[x] for x in verb_types if "intr." in x]
    for item in sublist
}
tr = {
    item["first_word"]
    for sublist in [verbs[x] for x in verb_types if "intr." not in x and "tr." in x]
    for item in sublist
}


def neighbor_letter_frequencies(word_list):
    all_neighbors = []

    for word in word_list:
        # Extract individual letters from the word
        letters = [letter.lower() for letter in word if letter.isalpha()]

        # Count occurrences of each pair of neighboring letters
        all_neighbors.extend(zip(letters, letters[1:]))

    neighbor_freq = Counter(all_neighbors)

    return neighbor_freq


result = neighbor_letter_frequencies(all_verbs)

# Print neighbor letter frequencies
result = sorted(result.items(), key=lambda x: x[1], reverse=True)  # (x[0][0], x[0][1]))
for neighbors, frequency in result:
    print(f"{neighbors[0]}{neighbors[1]}: {frequency} occurrences")

vobjs = []
for vclass in tqdm([x for x in verbs.keys()]):
    for vbt in verbs[vclass]:
        if vbt["first_word"] in ["pytá", "potar", "aûsub", "nhan", "nhe'eng", "porang", 'syb', 'ekar', "'u", 'abõ']:
            verb_obj = tupi.Verb(vbt["first_word"], vclass, vbt["definition"])
            vobjs.append(verb_obj)


def generate_permutations(input_list):
    # Use itertools.product to generate all possible pairs
    pairs = list(product(input_list, repeat=2))
    return pairs


# Example usage with your provided input
input_list = list(set(tupi.TupiAntigo.personal_inflections.keys()))
all_pairs = generate_permutations(input_list)

for v in sorted(
    [
        x
        for x in vobjs
        # if x.verbete in ["pytá", "potar", "aûsub", "nhan", "nhe'eng", "porang"]
    ],
    key=lambda x: x.verbete,
):
    test_cases_map = {
        "gerundio": [
            ("1ppi", "1ppi"),
            ("1ppi", "2ps"),
            ("1ppi", "2pp"),
            ("1ppi", "3p"),
            ("1ppe", "1ppe"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            ("1ps", "1ps"),
            ("1ps", "2ps"),
            ("1ps", "3p"),
            ("1ps", "2pp"),
            ("3p", "1ps"),
            ("3p", "2ps"),
            ("3p", "3p"),
            ("3p", "1ppi"),
            ("3p", "1ppe"),
            ("3p", "2pp"),
            ("2ps", "1ps"),
            ("2ps", "1ppi"),
            ("2ps", "1ppe"),
            ("2ps", "3p"),
            ("2pp", "1ps"),
            ("2pp", "1ppi"),
            ("2pp", "1ppe"),
            ("2pp", "3p"),
        ],
        "indicativo": [
            ("1ppi", "1ppi"),
            ("1ppi", "2ps"),
            ("1ppi", "2pp"),
            ("1ppi", "3p"),
            ("1ppe", "1ppe"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            ("1ps", "1ps"),
            ("1ps", "2ps"),
            ("1ps", "3p"),
            ("1ps", "2pp"),
            ("3p", "1ps"),
            ("3p", "2ps"),
            ("3p", "3p"),
            ("3p", "1ppi"),
            ("3p", "1ppe"),
            ("3p", "2pp"),
            ("2ps", "1ps"),
            ("2ps", "1ppi"),
            ("2ps", "1ppe"),
            ("2ps", "3p"),
            ("2pp", "1ps"),
            ("2pp", "1ppi"),
            ("2pp", "1ppe"),
            ("2pp", "3p"),
        ],
        "permissivo": [
            ("1ppi", "1ppi"),
            ("1ppi", "2ps"),
            ("1ppi", "2pp"),
            ("1ppi", "3p"),
            ("1ppe", "1ppe"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            ("1ps", "1ps"),
            ("1ps", "2ps"),
            ("1ps", "3p"),
            ("1ps", "2pp"),
            ("3p", "1ps"),
            ("3p", "2ps"),
            ("3p", "3p"),
            ("3p", "1ppi"),
            ("3p", "1ppe"),
            ("3p", "2pp"),
        ],
        "circunstancial": [
            ("1ppi", "1ppi"),
            ("1ppi", "2ps"),
            ("1ppi", "2pp"),
            ("1ppi", "3p"),
            ("1ppe", "1ppe"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            ("1ps", "1ps"),
            ("1ps", "2ps"),
            ("1ps", "3p"),
            ("1ps", "2pp"),
            ("3p", "1ps"),
            ("3p", "2ps"),
            ("3p", "3p"),
            ("3p", "1ppi"),
            ("3p", "1ppe"),
            ("3p", "2pp"),
        ],
        "imperativo": [
            ("2ps", "2ps"),
            ("2ps", "3p"),
            ("2pp", "2pp"),
            ("2pp", "3p"),
            ("2ps", "1ps"),
            ("2pp", "1ps"),
        ],
    }
    for modo, test_cases in [x for x in test_cases_map.items() if x[0] == 'gerundio']:
        print(f"{v.verbete} - {v.verb_class} ({modo})")
        # Print the result
        if v.transitivo:
            for subj, obj in test_cases:
                try:
                    v.conjugate(
                        subject_tense=subj,
                        object_tense=obj,
                        mode=modo,
                    )
                    # v.conjugate(
                    #     subject_tense=subj,
                    #     object_tense=obj,
                    #     dir_obj_raw="kurumim",
                    #     mode=modo,
                    # )
                except Exception as e:
                    print(f"\t({subj} -> {obj}):\tainda não desenvolvida", e)
        else:
            for subj in sorted({x[0] for x in test_cases}):
                try:
                    v.conjugate(
                        subject_tense=subj,
                        mode=modo,
                    )
                except Exception as e:
                    print(f"\t({subj} -> {obj}):\tainda não desenvolvida", e)

    # v.conjugate(subject_tense='1ps', object_tense='3p', mode='indicativo', pos='anteposto', pro_drop=False)
    # v.conjugate(subject_tense='1ps', object_tense='3p', mode='indicativo', pos='anteposto', pro_drop=False, dir_obj_raw='kunumin')
    # v.conjugate(subject_tense='1ps', object_tense='3p', mode='indicativo', pos='incorporado', pro_drop=False, dir_obj_raw='kunumin')
    # v.conjugate(subject_tense='1ps', object_tense='3p', mode='indicativo', pos='incorporado', pro_drop=True)
    # v.conjugate(subject_tense='1ps', object_tense='3p', mode='indicativo', pos='posposto', pro_drop=False)
    # v.conjugate(subject_tense='1ps', object_tense='1ps', mode='indicativo', pos='posposto', pro_drop=False)
    # v.conjugate(subject_tense='1ps', object_tense='1ps', mode='indicativo', pos='posposto', pro_drop=True)
    # v.conjugate(subject_tense='1ps', object_tense='2ps', mode='indicativo', pos='posposto', pro_drop=True)
    # v.conjugate(subject_tense='1ps', object_tense='2pp', mode='indicativo', pos='posposto', pro_drop=False)
    # v.conjugate(subject_tense='3p', object_tense='2pp', mode='indicativo', pos='posposto', pro_drop=False)
    # v.conjugate(subject_tense='3p', object_tense='1ps', mode='indicativo', pos='posposto', pro_drop=False, dir_obj_raw='îandé îara')
    # v.conjugate(subject_tense='2pp', object_tense='1ppi', mode='indicativo', pos='posposto', pro_drop=False)
    # v.conjugate(subject_tense='2ps', object_tense='1ps', mode='indicativo', pos='posposto', pro_drop=False)
    # v.conjugate(subject_tense='2pp', object_tense='2pp', mode='indicativo', pos='posposto', pro_drop=False)
    # v.conjugate(subject_tense='2pp', object_tense='2pp', mode='indicativo', pos='posposto', pro_drop=False, io_pref=True)
    # v.conjugate(subject_tense='3p', object_tense='3p', mode='indicativo', pos='posposto', pro_drop=False, io_pref=True)
    # break
