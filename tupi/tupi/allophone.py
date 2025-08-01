dat = [
    ["j", "ñ", "jt", "jnd", "j", "j"],
    ["w", "", "w", "", "w", ""],
    ["r", "n", "s", "", "r", "n"],
    ["nd", "n", "nd", "nd", "n", "n"],
    ["mb", "m", "mb", "mb", "m", "m"],
    ["k", "ng", "k", "ng", "k", "ng"],
    ["s", "nd", "s", "nd", "", ""],
    ["t", "nd", "t", "nd", "", ""],
    ["b", "b", "p", "", "b", ""],
    ["p", "mb", "p", "mb", "", ""],
    [
        "'",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "a",
        "ã",
        "",
        "",
        "á",
        "ã",
    ],
    [
        "e",
        "ẽ",
        "",
        "",
        "é",
        "ẽ",
    ],
    [
        "o",
        "õ",
        "",
        "",
        "ó",
        "õ",
    ],
    [
        "i",
        "ĩ",
        "j",
        "",
        "í",
        "ĩ",
    ],
    [
        "u",
        "ũ",
        "w",
        "",
        "ú",
        "ũ",
    ],
    [
        "y",
        "ỹ",
        "ŷ",
        "",
        "ý",
        "ỹ",
    ],
]

# get all of the unique strings in a set that appear in the dat matrix above
# this is a list of all the possible allophones
phonemes = set([x for y in dat for x in y if x != ""])
oral = [x[0] for x in dat]
compaba = [(x[1] if x[1] else x[0]) for x in dat]
compnasal = [(x[2] if x[2] else x[0]) for x in dat]
ending = [(x[3] if x[3] else x[0]) for x in dat]
endingnasal = [(x[4] if x[4] else x[0]) for x in dat]
# pretty print the phonemes in alfabetic order
for fon in sorted(phonemes):
    print(fon, end=" ")


class Allophone(object):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


if __name__ == "__main__":
    n = Allophone()
    print(n)
