import csv, os
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

def load_ort(ort):
    res = dict()
    with open(os.path.join(alt_ort_dir, f"{ort}.csv"), "r") as f:
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

load_all_ort()