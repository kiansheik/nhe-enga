import re

line = "aroane'ym2 (conj.) - em vez de, ao contrário de"

# The regex pattern to match:
# 1. the first word (group 1),
# 2. an optional number (group 2),
# 3. the part of speech in parenthesis (group 3),
# 4. the definition following the hyphen (group 4).
pattern = r"([\w']+?)(\d*)\s+\(([\w.]+)\)\s+-\s+(.*)"

match = re.search(pattern, line)

if match:
    first_word = match.group(1)
    optional_number = match.group(2)
    part_of_speech = match.group(3)
    definition = match.group(4)
    
    print(f"First word: {first_word}")
    print(f"Optional number: {optional_number}")
    print(f"Part of speech: {part_of_speech}")
    print(f"Definition: {definition}")
else:
    print("No match found.")
