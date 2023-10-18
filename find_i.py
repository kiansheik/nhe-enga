import json
from tqdm import tqdm
from unidecode import unidecode

# Function to normalize words by removing diacritics and replacing 'y' with 'i'
def normalize_word(word):
    word = unidecode(word)  # Remove diacritics
    word = word.lower()  # Convert to lowercase
    return word


def remove_i(word):
    word = word.replace("y", "i")
    return word


# Read JSON data from the file
file_path = "docs/tupi_dict_navarro.json"

with open(file_path, "r", encoding="utf-8") as file:
    json_data = json.load(file)

# Create a set to store normalized words that contain 'y' or 'i' (without diacritics)
words_with_y_or_i = list()

# Create a list to store pairs of identical partner words
identical_partner_word_pairs = []

# Populate the set with words that contain 'y' or 'i' (without diacritics)
for word_obj in tqdm(json_data):
    first_word = word_obj["first_word"]
    normalized_first_word = normalize_word(first_word)

    # Check if the normalized word contains 'y' or 'i'
    if "y" in normalized_first_word or "i" in normalized_first_word:
        words_with_y_or_i.append(word_obj)

# Iterate through the list of objects and compare words with each other
for word_obj in tqdm(words_with_y_or_i):
    first_word = word_obj["first_word"]
    normalized_first_word = normalize_word(first_word)
    no_i_first_word = remove_i(normalized_first_word)

    # Compare the first word with each word in the JSON list that has 'y' or 'i'
    for other_word_obj in words_with_y_or_i:
        other_word = other_word_obj["first_word"]
        normalized_other_word = normalize_word(other_word)
        no_i_other_word = remove_i(normalized_other_word)

        # Avoid comparing a word with itself and only compare if both words are in the set
        if (
            normalized_first_word != normalized_other_word
            and no_i_first_word == no_i_other_word
            and other_word not in word_obj["definition"]
            and first_word not in other_word_obj["definition"]
        ):
            # Found an identical partner word pair
            if (
                other_word,
                first_word,
                other_word_obj["definition"],
                word_obj["definition"],
            ) not in identical_partner_word_pairs:
                identical_partner_word_pairs.append(
                    (
                        first_word,
                        other_word,
                        word_obj["definition"],
                        other_word_obj["definition"],
                    )
                )
                # print((first_word, other_word))

# Remove duplicate entries from the list of pairs
unique_identical_partner_word_pairs = list(set(identical_partner_word_pairs))

# Print the results
for pair in unique_identical_partner_word_pairs:
    # Split the sample entry into its components
    word1, word2, definition1, definition2 = pair

    # Organize and format the output
    formatted_output = f"Word 1: {word1}\nWord 2: {word2}\n\nDefinition 1:\n{definition1}\n\nDefinition 2:\n{definition2}\n\n"

    print(formatted_output)
