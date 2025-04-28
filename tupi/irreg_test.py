import sys
sys.path.append('tupi')
import tupi
from tupi import IrregVerb

#!/usr/bin/env python -i
import json
from collections import Counter
from itertools import product
import random
from tqdm import tqdm
import matplotlib.pyplot as plt
import sys
sys.path.append('tupi')
import unicodedata
import gzip

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

# with open("docs/tupi_dict_navarro.js", "r") as file:
#     lines = file.readlines()
#     lines[0] = lines[0][lines[0].find("=") + 1 : -2]

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
# Parse the JSON data from 'docs/dict-conjugated.json' into a Python object
with open("../docs/tupi_dict_navarro.json", "r") as f:
    # use json to read from file
    dicc = json.load(f)

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
            "definition": definition,
            "id": vid,
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
    "(r, s) (xe) (v. da 2ª classe)",
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


vobjs = []
irregvobjs = []
othervobjs = []
for vclass in tqdm([x for x in verbs.keys()]):
    for vbt in verbs[vclass]:
        if vclass in [
            "(s) (v.tr.)",
            "(v.tr.)",
            "(v. intr.)",
            "(v. intr. compl. posp.)",
            "(v.tr. ou intr.)",
            "(s) (v.tr. e intr.)",
            "(v. da 2ª classe)",
            "(-îo-, -s-) (v.tr. irreg. Incorpora -îo- (ou -nho-) e -s- no indicativo e formas derivadas deste.)",
            "(xe) (r, s) (v. da 2ª classe)",
            "(r, s) (xe) (v. da 2ª classe)",
            "(-îo-) (v.tr.)",
            "(-îo- ou -nho-) (v.tr.)",
            "(-îo-s- ou -nho-s-) (v.tr. irreg. Incorpora -îo- e -s-. Nas formas nominais é pluriforme.)",
            "(v. tr. irreg.)",
            # "(v. intr. irreg.)",
            "(t) (v. intr. compl. posp. irreg.)",
            "(v. intr. irreg. usado somente no plural)",
            "(v.tr. irreg. - não recebe o pronome -î- incorporado)"
        ]:
            verb_obj = tupi.Verb(
                vbt["first_word"], vclass, vbt["definition"], vid=vbt["id"]
            )
            vobjs.append(verb_obj)
        if "(v. intr. irreg.)" in vclass:
            irregvobj = IrregVerb(
                vbt["first_word"], vclass, vbt["definition"], vid=vbt["id"]
            )
            irregvobjs.append(irregvobj)
        else:
            othervobj = tupi.Verb(
                vbt["first_word"], vclass, vbt["definition"], vid=vbt["id"]
            )
            othervobjs.append(othervobj)

# for all the v in irregvobjs, make a counter of the verb_class
irregvobjs_counter = Counter()
for v in irregvobjs:
    irregvobjs_counter.update([v.verb_class])

othervobjs_counter = Counter()
for v in othervobjs:
    othervobjs_counter.update([v.verb_class])

def generate_permutations(input_list):
    # Use itertools.product to generate all possible pairs
    pairs = list(product(input_list, repeat=2))
    return pairs


# Example usage with your provided input
input_list = list(set(tupi.TupiAntigo.personal_inflections.keys()))
all_pairs = generate_permutations(input_list)

modes = ["indicativo", "permissivo", "circunstancial", "gerundio", "imperativo"]
subj_pref_map = {
    "ø": None,
    "ixé": "1ps",
    "oré": "1ppe",
    "îandé": "1ppi",
    "endé": "2ps",
    "peẽ": "2pp",
    "a'e": "3p",
}
obj_pref_map = {
    "ø": None,
    "xe": "1ps",
    "oré": "1ppe",
    "îandé": "1ppi",
    "nde": "2ps",
    "pe": "2pp",
    "i": "3p",
}

conns = dict()

quiz = []
for v in tqdm(
    sorted(
        [
            x
            for x in irregvobjs
            # if x.verbete in ["endyîuî"]
        ],
        key=lambda x: x.verbete,
    )
):
    test_cases_map = {
        "indicativo": [
            # Ixe
            # ("1ps", "1ps"),
            ("1ps", "2ps"),
            ("1ps", "2pp"),
            ("1ps", "3p"),
            ("1ps", "refl"),
            # Oré
            # ("1ppe", "1ppe"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            ("1ppe", "refl"),
            ("1ppe", "mut"),
            # Îandé
            ("1ppi", "3p"),
            ("1ppi", "refl"),
            ("1ppi", "mut"),
            # Endé
            ("2ps", "1ps"),
            ("2ps", "1ppe"),
            # ("2ps", "2ps"),
            ("2ps", "3p"),
            ("2ps", "refl"),
            # pee
            ("2pp", "1ps"),
            ("2pp", "1ppe"),
            # ("2pp", "2pp"),
            ("2pp", "3p"),
            ("2pp", "refl"),
            ("2pp", "mut"),
            # a'e
            ("3p", "1ps"),
            ("3p", "1ppe"),
            ("3p", "1ppi"),
            ("3p", "2ps"),
            ("3p", "2pp"),
            ("3p", "3p"),
            ("3p", "refl"),
            ("3p", "mut"),
        ],
        "gerundio": [
            ("1ps", "1ps"),
            ("1ppe", "1ppe"),
            ("1ppi", "1ppi"),
            ("2ps", "2ps"),
            ("2pp", "2pp"),
            ("3p", "3p"),
            ("refl", "refl"),
            ("mut", "mut"),
        ],
        "circunstancial": [
            # ixe
            ("1ps", "refl"),
            ("1ps", "mut"),
            ("1ps", "1ppe"),
            ("1ps", "1ppi"),
            ("1ps", "2ps"),
            ("1ps", "2pp"),
            ("1ps", "3p"),
            # oré
            ("1ppe", "1ps"),
            ("1ppe", "refl"),
            ("1ppe", "mut"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            # iande
            ("1ppi", "1ps"),
            ("1ppi", "refl"),
            ("1ppi", "mut"),
            ("1ppi", "3p"),
            # a'e
            ("3p", "1ps"),
            ("3p", "1ppe"),
            ("3p", "1ppi"),
            ("3p", "2ps"),
            ("3p", "2pp"),
            ("3p", "3p"),
            ("3p", "refl"),
            ("3p", "mut"),
        ],
        "imperativo": [
            # ende
            ("2ps", "1ps"),
            ("2ps", "1ppe"),
            ("2ps", "2ps"),
            ("2ps", "3p"),
            # pe'e
            ("2pp", "1ps"),
            ("2pp", "1ppe"),
            ("2pp", "2pp"),
            ("2pp", "3p"),
        ],
    }
    test_cases_map["permissivo"] = test_cases_map["indicativo"]
    test_cases_map["conjuntivo"] = test_cases_map["indicativo"]
    for modo, test_cases in [(x[0], x[1]) for x in test_cases_map.items()]:
        deff = f"{v.verbete} - {v.raw_definition}"[:200]
        # print(f"{v.verbete} - {v.verb_class} ({modo})")
        # Print the result
        if v.transitivo:
            for subj, obj in test_cases:
                try:
                    res = v.conjugate(
                        subject_tense=subj if modo != 'gerundio' else None,
                        object_tense=obj,
                        mode=modo,
                    )
                    neg_res = v.conjugate(
                        subject_tense=subj if modo != 'gerundio' else None,
                        object_tense=obj,
                        mode=modo,
                        negative=True
                    )
                    if (subj, obj) in test_cases_map[modo]:
                        quiz.append(
                            {
                                "f": res,
                                "s": subj if modo[:2] != "ge" else None,
                                "o": obj,
                                "m": modo[:2],
                                "d": deff,
                            }
                        )
                    dicc_con = {
                        "f": res,
                        "s": subj if modo[:2] != "ge" else None,
                        "o": obj,
                        "m": modo[:2], 'n': neg_res
                    }
                    if "con" in dicc_dict[v.vid]:
                        dicc_dict[v.vid]["con"].append(dicc_con)
                        conns[v.verbete+" "+str(v.vid)].append(dicc_con)

                    else:
                        dicc_dict[v.vid]["con"] = [dicc_con]
                        conns[v.verbete+" "+str(v.vid)] = [dicc_con]
                except Exception as e:
                    pass
                    print(f"\t({subj} -> {obj}):\tainda não desenvolvida", e)
        else:
            for subj in sorted({x[0] for x in test_cases}):
                try:
                    res = v.conjugate(
                        subject_tense=subj,
                        mode=modo,
                    )
                    neg_res = v.conjugate(
                        subject_tense=subj,
                        mode=modo,
                        negative=True
                    )
                    if subj in {x[0] for x in test_cases_map[modo]}:
                        quiz.append(
                            {"f": res, "s": subj, "o": None, "m": modo[:2], "d": deff}
                        )
                    dicc_con = {"f": res, "s": subj, "o": None, "m": modo[:2], 'n': neg_res}
                    if "con" in dicc_dict[v.vid]:
                        dicc_dict[v.vid]["con"].append(dicc_con)
                        conns[v.verbete+" "+str(v.vid)].append(dicc_con)

                    else:
                        dicc_dict[v.vid]["con"] = [dicc_con]
                        conns[v.verbete+" "+str(v.vid)] = [dicc_con]
                except Exception as e:
                    pass
                    print(f"\t({subj}:\tainda não desenvolvida", e)

















# def compress_data(data):
#     # Convert to JSON
#     json_data = json.dumps(data, separators=(',', ':'))
#     # Convert to bytes
#     encoded = json_data.encode('utf-8')
#     # Compress
#     return gzip.compress(encoded)

# with open("quiz/quiz.json.gz", "wb") as f:
#     c_quiz = compress_data(quiz)
#     f.write(c_quiz)

processed_data = [
    {k[0]:v for k,v in obj.items()}
    for obj in dicc_dict.values()
    if "con" in obj
]
# with open("docs/dict-conjugated.json.gz", "wb") as f:
#     c_data = compress_data(processed_data)
#     f.write(c_data)

# write conns to json
with open("/Users/kian/Downloads/conns.json", "w") as f:
    json.dump(conns, f, indent=4)