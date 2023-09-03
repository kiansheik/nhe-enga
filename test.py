from docx import Document
import sys, re

def find_string_in_docx(docx_file, target_string):
    doc = Document(docx_file)
    occurrences = []

    lines_per_page = 25  # Adjust this value based on your document's formatting

    current_page = 1
    lines_count = 0

    for para in doc.paragraphs:
        if target_string in para.text:
            occurrences.append((current_page, para.text))
        
        lines_count += 1
        if lines_count >= lines_per_page:
            lines_count = 0
            current_page += 1

    return occurrences

def parse_verbete(line):
    pattern = r"([\w']+?)(\d*)\s+\(([\w.]+)\)\s+-\s+(.*)"

    match = re.search(pattern, line)

    if match:
        first_word = match.group(1)
        optional_number = match.group(2)
        part_of_speech = match.group(3)
        definition = match.group(4)
        
        # print(f"First word: {first_word}")
        # print(f"Optional number: {optional_number}")
        # print(f"Part of speech: {part_of_speech}")
        # print(f"Definition: {definition}")
        return (first_word, optional_number if optional_number else None, part_of_speech, definition)
    return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <target_string>")
        sys.exit(1)

    docx_file_path = "docs/tupi-dic-cop.docx"
    target_string = sys.argv[1]

    found_occurrences = find_string_in_docx(docx_file_path, target_string)
    
    if found_occurrences:
        print("Occurrences found:")
        for idx, (page_number, occurrence) in enumerate(found_occurrences, start=1):
            # print(f"{idx}. Page {page_number}, Paragraph:")
            # print(occurrence.encode("utf-8").decode("utf-8"))
            # print("=" * 20)
            result = parse_verbete(occurrence.encode("utf-8").decode("utf-8"))
            if result:
                # if result[0] == target_string:
                print(f"{result[0]} {result[1] if result[1] else ''} ({result[2]}) - {result[3]}")
                    # break
    else:
        print("No occurrences found.")
