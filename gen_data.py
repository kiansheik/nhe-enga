import json
import re
import sys

from docx import Document


def find_string_in_docx(docx_file):
    doc = Document(docx_file)
    occurrences = []

    for para in doc.paragraphs:
        raw_text = para.text.encode("utf-8").decode("utf-8").strip()
        parsed = parse_verbete(raw_text)
        if parsed:
            occurrences.append(parsed)

    return occurrences


def parse_verbete(line):
    pattern = r"^([\w'!?.,();:-]+?)(\d*)\s+(.*)"

    match = re.search(pattern, line)
    out = dict()
    if match:
        out["first_word"] = match.group(1)
        out["optional_number"] = match.group(2)
        out["definition"] = match.group(3)
        return out
    return None


if __name__ == "__main__":
    docx_file_path = "docs/tupi-dic-cop.docx"

    found_occurrences = find_string_in_docx(docx_file_path)
    print(f"window.jsonData = {json.dumps(found_occurrences)};")
    # now save the occurrences to a file
    with open("docs/tupi_dict_navarro.json", "w") as f:
        f.write(json.dumps(found_occurrences))
