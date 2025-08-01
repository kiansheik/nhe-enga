# read dictionary
import json
import pdfplumber
import re
from copy import deepcopy
from tqdm import tqdm
import gzip
import pprint
from collections import Counter
import unicodedata


def extract_trailing_int(s):
    """
    Extracts a trailing integer from a string.

    Args:
        s (str): Input string.

    Returns:
        tuple: (str, int or None) where the string has the integer removed (if present),
               and the integer if found, otherwise None.
    """
    match = re.search(r"(\d+)$", s)  # Matches digits at the end of the string
    if match:
        trailing_int = int(match.group(1))  # Extract the integer
        stripped_string = s[: match.start()]  # Remove the integer from the string
        return stripped_string, trailing_int
    return s, None


pdf_path = "docs/primary_sources/GNDicLex.pdf"


def compress_data(data):
    # Convert to JSON
    json_data = json.dumps(data, separators=(",", ":"))
    # Convert to bytes
    encoded = json_data.encode("utf-8")
    # Compress
    return gzip.compress(encoded)


def get_indentation(line):
    """Calculate the indentation level of a line by measuring leading spaces."""
    return len(line) - len(line.lstrip())


cid_map = {
    "AFDFET+TTE29B13D0t00": {"(cid:1)": "ç"},
    "AGEFET+TTE2A45118t00": {
        "(cid:1)": "ĩ",
        "(cid:2)": "ũ",
        "(cid:3)": "ỹ",
        "(cid:4)": "ẽ",
    },
    "FWSEET+TTE2A45898t00": {
        "(cid:1)": "ĩ",
        "(cid:2)": "ỹ",
        "(cid:3)": "ẽ",
        "(cid:4)": "ũ",
    },
    "IYBEET+TTE299D410t00": {"(cid:1)": " "},
    "JGLEET+TTE2A45DA8t00": {"(cid:1)": "ẽ"},
    "NDZEET+TTE2AA58D8t00": {
        "(cid:1)": "-",
        "(cid:10)": "a",
        "(cid:11)": "m",
        "(cid:12)": "\u0303",
        "(cid:13)": "j",
        "(cid:14)": "i",
        "(cid:15)": "p",
        "(cid:16)": "o",
        "(cid:17)": "k",
        "(cid:18)": "ŋ",
        "(cid:19)": "u",
        "(cid:2)": "a",
        "(cid:20)": "n",
        "(cid:21)": "e",
        "(cid:22)": "\u0301",
        "(cid:23)": "y",
        "(cid:24)": "w",
        "(cid:25)": "\u030C",
        "(cid:26)": "ɨ",
        "(cid:27)": ".",
        "(cid:28)": "\u0303",
        "(cid:29)": "",
        "(cid:3)": "\u0301",
        "(cid:30)": "ɨ",
        "(cid:4)": "β",
        "(cid:5)": " ",
        "(cid:6)": "c",
        "(cid:7)": "t",
        "(cid:8)": "r",
        "(cid:9)": "ʔ",
    },
    "ZBPFET+TTE2A43390t00": {
        "(cid:1)": "ĩ",
        "(cid:2)": "ỹ",
        "(cid:3)": "ẽ",
        "(cid:4)": "ũ",
    },
}


def normalize(text):
    return unicodedata.normalize("NFC", text.strip())


def parse_dictionary_with_indentation(pdf_path):
    parsed_data = []
    current_entry = None
    is_verbete = False
    current_definition = ""
    current_verbete = ""
    last_x0 = 0
    size_counter = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in tqdm(pdf.pages):
            for elem in page.parse_objects()["char"]:
                letter, font, color, x0 = (
                    elem["text"],
                    elem["fontname"],
                    elem["stroking_color"],
                    elem["x0"],
                )
                # if "cid" in letter:
                #     cid_map[font] = cid_map.get(font, dict())
                #     cid_map[font][letter] = ""
                lat = cid_map.get(font, dict()).get(
                    letter, letter.replace("cid:", f"{font}:cid:")
                )
                if lat:
                    letter = lat
                # if "cid" in letter:
                #     breakpoint()
                if (
                    last_x0 > x0
                    and color == (0, 0, 1)
                    and "bold" in font.lower()
                    and int(elem["size"]) == 10
                ):
                    size_counter.append(elem["size"])
                    if current_verbete:
                        current_verbete = normalize(current_verbete)
                        vbt, num = extract_trailing_int(current_verbete)
                        current_entry = {
                            "verbete": vbt,
                            "definition": normalize(current_definition),
                            "number": num,
                        }
                        parsed_data.append(deepcopy(current_entry))
                    is_verbete = True
                    current_verbete = letter
                    current_definition = ""
                elif is_verbete and color == (0, 0, 1):
                    current_verbete += letter
                else:
                    is_verbete = False
                    current_definition += letter
                last_x0 = x0
    current_verbete = normalize(current_verbete)
    vbt, num = extract_trailing_int(current_verbete)
    current_entry = {
        "verbete": vbt,
        "definition": normalize(current_definition),
        "number": num,
    }
    parsed_data.append(deepcopy(current_entry))
    # print(Counter(size_counter))
    return parsed_data


# pages = []
# pdf = pdfplumber.open(pdf_path)
# for page in pdf.pages:
#     pages.append(page)


# Parse the dictionary
parsed_data = parse_dictionary_with_indentation(pdf_path)

# Save to a JSON file or print the output
output_path = "docs/dooley_2006_mbya_dic.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=4)

# Save the modified data to a new JSON file as .tar.gz
compressed_data = compress_data(
    [{"f": x["verbete"], "d": x["definition"], "o": x["number"]} for x in parsed_data]
)
with open("docs/dooley_2006_mbya_dic.json.gz", "wb") as f:
    f.write(compressed_data)

print(f"Parsed dictionary saved to {output_path}")

# pprint.pprint(cid_map)
