# read dictionary
import json
import pdfplumber
import re
from copy import deepcopy
from tqdm import tqdm
import gzip

pdf_path = "docs/primary_sources/GNDicLex.pdf"

def compress_data(data):
    # Convert to JSON
    json_data = json.dumps(data, separators=(',', ':'))
    # Convert to bytes
    encoded = json_data.encode('utf-8')
    # Compress
    return gzip.compress(encoded)

def get_indentation(line):
    """Calculate the indentation level of a line by measuring leading spaces."""
    return len(line) - len(line.lstrip())

def parse_dictionary_with_indentation(pdf_path):
    parsed_data = []
    current_entry = None
    is_verbete = False
    current_definition = ""
    current_verbete = ""
    last_x0 = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page in tqdm(pdf.pages):
            for elem in page.parse_objects()['char']:
                letter, font, color, x0 = elem['text'], elem['fontname'], elem['stroking_color'], elem['x0']
                if last_x0 > x0 and color == (0, 0, 1) and font == 'Times-Bold':
                    if current_verbete:
                        current_entry = {"verbete": current_verbete.strip(), "definition": current_definition.strip()}
                        parsed_data.append(deepcopy(current_entry))
                    is_verbete = True
                    current_verbete = letter
                    current_definition = ""
                elif is_verbete and color == (0, 0, 1) and font == 'Times-Bold':
                    current_verbete += letter
                else:
                    is_verbete = False
                    current_definition += letter
                last_x0 = x0
    current_entry = {"verbete": current_verbete.strip(), "definition": current_definition.strip()}
    parsed_data.append(deepcopy(current_entry))
    return parsed_data

# pages = []
# pdf = pdfplumber.open(pdf_path)
# for page in pdf.pages:
#     pages.append(page)


# Parse the dictionary
parsed_data = parse_dictionary_with_indentation(pdf_path)

# Save to a JSON file or print the output
output_path = 'docs/dooley_2006_mbya_dic.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=4)

# Save the modified data to a new JSON file as .tar.gz
compressed_data = compress_data([{"f":x["verbete"], "d":x["definition"]} for x in parsed_data])
with open("docs/dooley_2006_mbya_dic.json.gz", "wb") as f:
    f.write(compressed_data)

print(f"Parsed dictionary saved to {output_path}")
