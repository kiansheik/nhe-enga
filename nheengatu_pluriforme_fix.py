import re
import json
import gzip

json_path = "docs/extracted_entries_nheengatu.json"


def extract_text(input_string):
    match = re.match(r"^[^\(\[\{]+", input_string)
    if match:
        return match.group(0).strip()
    return input_string.strip()


# Example usage
input_string = "fewf (r, t, [T})"
result = extract_text(input_string)
print(result)  # Output: fewf

# Load the JSON file
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

new_data = []
for entry in data:
    word = extract_text(entry["word"])
    definition = entry["definition"]
    if word != entry["word"]:
        # prepend the difference between the original word and the extracted word onto the definition
        print(f"Original: {entry['word']}, Extracted: {word}")
        definition = f"{entry['word'].replace(word, '').strip()} {definition}"
    new_data.append({"f": word, "d": definition})


def compress_data(data):
    # Convert to JSON
    json_data = json.dumps(data, separators=(",", ":"))
    # Convert to bytes
    encoded = json_data.encode("utf-8")
    # Compress
    return gzip.compress(encoded)


# Save the modified data to a new JSON file as .tar.gz
compressed_data = compress_data(new_data)
with open("docs/extracted_entries_nheengatu.tar.gz", "wb") as f:
    f.write(compressed_data)
