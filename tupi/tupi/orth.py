import csv, os, json
source_dir = os.path.dirname(os.path.abspath(__file__))
alt_ort_dir = os.path.join(source_dir, "alt_ort")
ANCHIETA_1 = {
    # Processed
    # Glottal stops
    "'a": "â",
    "'á": "â",
    "'e": "ê",
    "'é": "ê",
    "'i": "î",
    "'í": "î",
    "'y": "î",
    "'ý": "î",
    "'o": "ô",
    "'ó": "ô",
    "'u": "û",
    "'ú": "û",
    "'ã": "â",
    "'ẽ": "ê",
    "'ĩ": "î",
    "'ỹ": "î",
    "'õ": "ô",
    "'ũ": "û",

    # Nasal Vowels
    "ã": "â",
    "ẽ": "ê",
    "ĩ": "î",
    "ỹ": "î",
    "õ": "ô",
    "ũ": "û",

    # Accented vowels
    "á": "à",
    "é": "è",
    "í": "ì",
    "ý": "î",
    "ó": "ò",
    "ú": "ù", 

    # Normal vowels
    "a": "a",
    "e": "e",
    "i": "i",
    "y": "î",
    "o": "o",
    "u": "u",

    # k sounds
    "ka": "ca",
    "ko": "co",
    "ku": "cu",
    "ke": "que",
    "ki": "qui",
    "ky": "quî",

    # s sounds
    "s": "ç",
    "se": "ce",
    "sé": "cè",
    "si": "ci",
    "sy": "cî",
    "x": "x",

    # semi-vowels
    "û": "gu",
    "gû": "gu",
    "î": "y",
    "îy": "gi",
    "ŷ": "y",

    # Cw
    "pû": "po",
    "mbû": "mbo",
    "ngû": "ngo",
    "sû": "so",
    "mû": "mo",
    "ndû": "ndo",
    "kû": "co",


    # # Unprocessed
    "pî": "py",
    "nh": "nh",
    "ng": "ng",
    "mb": "mb",
    "nd": "nd",
    "ng": "ng",
    "p": "p",
    "b": "b",
    "t": "t",
    "'": "",
    "m": "m",
    "n": "n",
    "r": "r",
    "g": "g",
}

ALT_ORTS = dict()
ALT_ORTS["ANCHIETA_1"] = ANCHIETA_1
nasais = "m n nh ng ã ẽ ĩ ỹ õ ũ mb nd".split(" ")
consoantes = "p b t s x k ' m n r nh ng mb nd ng g û î ŷ".split(" ")
def load_ort(ort):
    res = dict()
    with open(os.path.join(alt_ort_dir, f"{ort}.csv"), "r", encoding="utf-8") as f:
        # skip header of f, column 0 is the keys of the dict, column 1 the values of PHONEMIC_OT_FINBOW
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            res[row[0]] = row[1]
    ALT_ORTS[ort] = res

# search the folder alt_ort for all ort files, strip the .csv
def load_all_ort():
    for file in os.listdir(alt_ort_dir):
        if file.endswith(".csv"):
            load_ort(file[:-4])

with open(os.path.join(alt_ort_dir, "nasal_cluster_scores.json"), "r", encoding="utf-8") as f:
    help_score = json.load(f)

def calculate_weighted_nasality_probability(string):
    # Sort clusters by length in descending order to prioritize longer matches
    if string == "":
        return 0.0
    clusters = sorted(help_score.keys(), key=len, reverse=True)
    weighted_sum = 0.0
    for cluster in clusters:
        if string.startswith(cluster):
            # Calculate the weight as the proportional size of the cluster
            pass_rate = help_score[cluster]['influence']
            # Update the weighted sum and total weight
            weighted_sum += pass_rate
    return weighted_sum

def get_nasality_î(string, idx):
    if idx == len(string) - 1:
        return "î"
    # Define consonants (modify as needed based on your requirements)
    # Check if there is a consonant to the left or right of idx
    if (idx > 0 and string[idx - 1] in consoantes) or (idx < len(string) - 1 and string[idx + 1] in consoantes):
        return "î"
    left_most_nasal = idx
    x = string[left_most_nasal:]
    while True not in ([x.startswith(nas) for nas in (nasais)]) and x != "":
        left_most_nasal += 1
        x = string[left_most_nasal:]
    if x == "":
        return "î"
    search_space = string[idx+1:left_most_nasal]
    score = calculate_weighted_nasality_probability(search_space)
    if score < 0:
        return "î"
    return "nh"


load_all_ort()

if __name__ == "__main__":
    for word in ["rãî", "rãîã", "emonhangaîn"]:
        print(get_nasality_î(word, word.index("î")))