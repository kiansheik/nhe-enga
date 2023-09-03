from docx import Document
import sys, re, json

def find_string_in_docx(docx_file, target_string):
    doc = Document(docx_file)
    occurrences = []

    lines_per_page = 25  # Adjust this value based on your document's formatting

    current_page = 1
    lines_count = 0

    for para in doc.paragraphs:
        parsed = parse_verbete(para.text.encode("utf-8").decode("utf-8"))
        if parsed:
            occurrences.append(parsed)
        
        lines_count += 1
        if lines_count >= lines_per_page:
            lines_count = 0
            current_page += 1

    return occurrences

def parse_verbete(line):
    pattern = r"([\w']+?)(\d*)\s+\(([\w.]+)\)\s+-\s+(.*)"

    match = re.search(pattern, line)
    out = dict()
    if match:
        out['first_word'] = match.group(1)
        out['optional_number'] = match.group(2)
        out['part_of_speech'] = match.group(3)
        out['definition'] = match.group(4)
        return out
    return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <target_string>")
        sys.exit(1)

    docx_file_path = "docs/tupi-dic-cop.docx"
    target_string = sys.argv[1]

    found_occurrences = find_string_in_docx(docx_file_path, target_string)
    print(json.dumps(found_occurrences))
