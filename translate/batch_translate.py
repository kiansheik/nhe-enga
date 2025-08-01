import copy
import re
import json, gzip
import unicodedata
import requests
from ratelimit import limits, sleep_and_retry
import anthropic
import csv

# Define rate limits
ONE_MINUTE = 60
ONE_DAY = 86400  # 24 hours in seconds

greenlit = (
    "AIzaSyBpMxS3A2AcdkgjN5BBaZQJpqcBg79MVtE"  # Not safe but for a free access account
)

system = (
    "You are a linguist for tupi-guaranian languages. I will give you an old tupi/tupinambá sentence in addition to a lengthty linguistic analysis. The definitions are in portuguese.\n"
    f"I am looking for the most natural translation which would get the meaning across in the target language listed in the prompt, not a word-for-word translation.\n"
    "Without describing your rationale, give me 5 potential translations in separate lines"
)

with open("tag_prompt_map.json", "r") as f:
    tag_prompt_map = json.load(f)


@sleep_and_retry
@limits(calls=15, period=ONE_MINUTE)
@limits(calls=1500, period=ONE_DAY)
def get_ai_response(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={greenlit}"

    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "safetySettings": [
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    }

    response = requests.post(url, json=request_body)

    if response.status_code == 200:
        data = response.json()
        # Extract and return only the text content
        return data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        response.raise_for_status()


def extract_and_concat_definitions(definitions_text):
    pattern = r"([0-9a-z])\)\s*([A-Za-zÀ-ÖØ-öø-ÿ\s,'-]{4,})"
    matches = re.findall(pattern, definitions_text)
    # Concatenate matches with the number/letter as a prefix
    concatenated_definitions = "\n".join(
        [f"\t{match[0]}) {match[1]}" for match in matches]
    )
    return concatenated_definitions


def format_verbetes(verbetes):
    formatted_verbetes = []
    for verbete in verbetes:
        # Extract and concatenate definitions
        full_definition = extract_and_concat_definitions(verbete["d"])
        # Use concatenated definition if available, otherwise fallback to the raw definition
        definition_to_use = full_definition.strip()
        if not definition_to_use or not definition_to_use.startswith("1)"):
            definition_to_use = verbete["d"].split(":")[0].strip()
        # Format as "optional_number. first word - definition"
        formatted = f"{verbete.get('optional_number', '')} {verbete['f']} - {definition_to_use}".strip()
        formatted_verbetes.append(formatted)
    return formatted_verbetes


def format_verbetes_all(verbetes):
    formatted_verbetes = []
    for verbete in verbetes:
        # Extract and concatenate definitions
        full_definition = verbete["d"]
        # Use concatenated definition if available, otherwise fallback to the raw definition
        definition_to_use = full_definition.strip()
        # Format as "optional_number. first word - definition"
        formatted = f"{verbete.get('optional_number', '')} {verbete['f']} - {definition_to_use}".strip()
        formatted_verbetes.append(formatted)
    return formatted_verbetes


def remove_diacritics(input_str):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", input_str)
        if unicodedata.category(c) != "Mn"
    )


def search_by_first_word_no_accent(data, query):
    query_normalized = remove_diacritics(query.lower())
    return [
        item
        for item in data
        if remove_diacritics(item["f"].lower()) == query_normalized
    ]


def search_by_first_word_no_accent_no_a(data, query):
    query_normalized = remove_diacritics(query.lower())
    return [
        item
        for item in data
        if remove_diacritics(item["f"].lower()[:-1]) == query_normalized
    ]


def get_root_defs(root_words, dictionary):
    verbete_results_diacritic = []
    for root_word in root_words:
        core_root = root_word.replace(" ", "")
        verbete_results = search_by_first_word_no_accent(
            dictionary, core_root
        ) + search_by_first_word_no_accent_no_a(dictionary, core_root)
        verbete_results_diacritic.extend(verbete_results)

    return verbete_results_diacritic


def get_root_defs_all(root_words, dictionary):
    verbete_results_diacritic = []
    for root_word in root_words:
        core_root = root_word.replace(" ", "")
        verbete_results = search_by_first_word_no_accent(
            dictionary, core_root
        ) + search_by_first_word_no_accent_no_a(dictionary, core_root)
        verbete_results_diacritic.extend(verbete_results)

    return verbete_results_diacritic


# load the dictionary file in ../docs/dict-conjugated.json.gz
with gzip.open("../docs/dict-conjugated.json.gz", "rt") as f:
    dictionary = json.load(f)
    # rename


def parse_parts(input_text):
    regex = r"([^\[]*)\s*(\[[^\]]+\])"
    result = []

    for match in re.finditer(regex, input_text):
        part1 = match.group(1).strip()  # Text before the bracket, can be empty
        part2 = match.group(2)  # Text within the bracket

        # Handle the case where part1 is empty
        if not part1:
            part1 = ""  # Ensure part1 is an empty string if nothing was found

        # Add both parts (including empty part1) to the result
        result.append([part1.replace(" ", ""), part2.replace(" ", "")])

    return result


def classify_parts(parts):
    base_verb_data = {
        "subject": "",
        "subject_tense": "",
        "object": "",
        "object_tense": "",
        "negative": False,
        "permissive": False,
        "imperative": False,
        "gerund": False,
        "root": "",
    }

    verb_data = copy.deepcopy(base_verb_data)
    verb_on = False
    verb_objs = []

    for part, tag in parts:
        if "[MAIN_VERB]" in tag or "[SUB_VERB]" in tag:
            verb_on = not verb_on
            if verb_on:
                verb_data = copy.deepcopy(base_verb_data)
            else:
                if "[MAIN_VERB]" in tag:
                    verb_objs.insert(0, verb_data)
                else:
                    verb_objs.append(verb_data)
            continue

        if "[SUBJECT:1ps]" in tag or "[SUBJECT_PREFIX:1ps]" in tag:
            verb_data["subject_tense"] += "1st person singular - I"
        elif "[SUBJECT:1ppe]" in tag or "[SUBJECT_PREFIX:1ppe]" in tag:
            verb_data[
                "subject_tense"
            ] += "1st person plural (excluding 2nd person) - we, not you"
        elif "[SUBJECT:1ppi]" in tag or "[SUBJECT_PREFIX:1ppi]" in tag:
            verb_data[
                "subject_tense"
            ] += "1st person plural (including 2nd person) - we all"
        elif (
            "[SUBJECT:2ps]" in tag
            or "[SUBJECT_PREFIX:2ps]" in tag
            or "[IMPERATIVE_PREFIX:2ps]" in tag
        ):
            verb_data["subject_tense"] += "2nd person singular - you"
        elif (
            "[SUBJECT:2pp]" in tag
            or "[SUBJECT_PREFIX:2pp]" in tag
            or "[IMPERATIVE_PREFIX:2pp]" in tag
        ):
            verb_data["subject_tense"] += "2nd person plural - y'all"
        elif "[SUBJECT:3p]" in tag or "[SUBJECT_PREFIX:3p]" in tag:
            verb_data[
                "subject_tense"
            ] += "3rd person (singular or plural) - He/She/It/They"
        elif "[SUBJECT:2ps:OBJECT_1P]" in tag:
            verb_data["subject_tense"] += "2nd person singular - you"
            verb_data["object_tense"] += "1st person - me/us"
        elif "[SUBJECT:2pp:OBJECT_1P]" in tag:
            verb_data["subject_tense"] += "2nd person plural - y'all"
            verb_data["object_tense"] += "1st person - me/us"

        if "[SUBJECT:" in tag:
            verb_data["subject"] = part

        if "[OBJECT:2ps:SUBJECT_1P]" in tag:
            verb_data["subject_tense"] += "1st person - I/we"
            verb_data["object_tense"] += "2nd person singular - you"
        elif "[OBJECT:2pp:SUBJECT_1P]" in tag:
            verb_data["subject_tense"] += "1st person - I/we"
            verb_data["object_tense"] += "2nd person plural - y'all"
        elif "[OBJECT:1ppi]" in tag:
            verb_data[
                "object_tense"
            ] += "1st person plural (including 2nd person) - us all"
        elif "[OBJECT:1ppe]" in tag:
            verb_data[
                "object_tense"
            ] += "1st person plural (excluding 2nd person) - us, not you"
        elif "[OBJECT:2ps]" in tag:
            verb_data["object_tense"] += "2nd person singular - you"
        elif "[OBJECT:2pp]" in tag:
            verb_data["object_tense"] += "2nd person plural - y'all"
        elif "[OBJECT:3p]" in tag:
            verb_data[
                "object_tense"
            ] += "3rd person (singular or plural) - Him/Her/It/Them"
        elif "[OBJECT:1ps]" in tag:
            verb_data["object_tense"] += "1st person singular - me"
        elif "[PLURIFORM_PREFIX:S]" in tag or "OBJECT_MARKER:3p" in tag:
            verb_data[
                "object_tense"
            ] += "3rd person (singular or plural) - Him/Her/It/Them"
        elif "[OBJECT:REFLEXIVE]" in tag:
            verb_data["object_tense"] += "Reflexive - to oneself"
        elif "[OBJECT:MUTUAL]" in tag:
            verb_data["object_tense"] += "Mutual - to one another"

        if "[OBJECT:DIRECT]" in tag or "[OBJECT:3p]" in tag:
            verb_data["object"] = part

        if "NEGATION" in tag:
            verb_data["negative"] = True
        if "PERMISSIVE" in tag:
            verb_data["permissive"] = True
        if "IMPERATIVE" in tag:
            verb_data["imperative"] = True
        if "GERUND" in tag:
            verb_data["gerund"] = True
        if "[ROOT]" in tag:
            verb_data["root"] = part

    formatted_description = ""
    for i, vd in enumerate(verb_objs):
        formatted_description += (
            "Main Verb: (present or past tense) " if i == 0 else "Auxiliary Verb: "
        )
        formatted_description += f"{vd['root']}\n"
        if vd["gerund"]:
            vd["subject_tense"] = ""
            vd["subject"] = "Same subject as Main Verb"
        formatted_description += f"Subject Noun: {vd['subject'] or ''}"
        if vd["subject_tense"]:
            formatted_description += f" Type({vd['subject_tense']})"  #'3rd person (singular or plural) - He/She/It/Them'
        if vd["object"] or vd["object_tense"]:
            if vd["object"]:
                vd["object"] = f"{vd['object']} (proper noun)"
            formatted_description += (
                f"\nObject Noun: {vd['object'] or vd['object_tense']}"
            )
        if vd["negative"]:
            formatted_description += f"\nThe verb '{vd['root']}' is negated."
        if vd["permissive"]:
            main_use = "Used to show wishes/hopes 'I hope that [VERB]'"
            sub_use = "Used to show finality when used as a subordinate clause '[MAIN_VERB] in order to ... [SUB_VERB]'"
            formatted_description += f"\nThe verb '{vd['root']}' is in a subjunctive mood. {main_use if i == 0 else sub_use}"
        if vd["imperative"]:
            formatted_description += f"\nThe verb '{vd['root']}' is in an imperative mood, used to give commands 'DO [MAIN_VERB]'."
        if vd["gerund"]:
            formatted_description += f"\nThe verb '{vd['root']}' is in a form used to show continuous and/or simultaneous actions '[MAIN_VERB] while [SUB_VERB]ing'. It can also represent finality '[MAIN_VERB] in order to [SUB_VERB]' or cause '[SUB_VERB] happened, causing [MAIN_VERB]', depending on the context."

        formatted_description += "\n\n"

    return "\n" + formatted_description


def find_root_words(parts_list):
    root_words = [
        part
        for part, tag in parts_list
        if tag == "[ROOT]"
        or ("DIRECT" in tag and ("SUBJECT" in tag or "OBJECT" in tag))
        or ("OBJECT:3p" in tag and part not in ["a'e", "i", "î"])
    ]
    return root_words


def generate_gpt_prompt(
    original_sentence, annotated_sentence, verbetes, target_language
):
    prompt = (
        "target language: " + target_language + "\n"
        f"The following source sentence is in Old Tupi: {original_sentence}\n"
        f"\n{annotated_sentence}\n"
        f"The roots, direct objects, and direct subjects which appear in the sentence have the following dictionary entries (there may be superfluous entries, decide which one applies most given the context):\n"
        + "\n".join([f"* {entry}\n" for entry in verbetes])
        + "\n\n"
    )
    return prompt


def clean_annotation(annotated):
    # Step 1: Remove bracketed content
    cleaned_text = re.sub(r"\[.*?\]", "", annotated)
    if "   " in cleaned_text:
        # Step 2: Replace 3 or more spaces with a placeholder [SPACE]
        cleaned_text = re.sub(r"\s{3,}", "[SPACE]", cleaned_text)
        # Step 3: Remove all remaining spaces
        cleaned_text = re.sub(r"\s+", "", cleaned_text)
    # Step 4: Replace [SPACE] with a single space
    return cleaned_text.replace("[SPACE]", " ")


@sleep_and_retry
@limits(calls=7, period=ONE_MINUTE)
def anthropicResponse(prompt):
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    )
    return message.content[0].text


def classify_parts_json(parts):
    exceptions = ["[SUBJECT:3p:DIRECT]", "[ROOT]", "[OBJECT:DIRECT]"]
    resp = ""
    main_verb = False
    sub_verb = False
    for part in parts:
        if part[1] == "[MAIN_VERB]":
            main_verb = not main_verb
            if main_verb:
                resp += "Main Verb Breakdown:\n"
            else:
                resp += "\n"
        elif part[1] == "[SUB_VERB]":
            sub_verb = not sub_verb
            if sub_verb:
                resp += "Subordinate Verb Breakdown:\n"
            else:
                resp += "\n"
        else:
            found = False
            for tag in tag_prompt_map:
                if (part[0] == tag["value"] and part[1] == tag["tag"]) or (
                    part[1] in exceptions and tag["tag"] == part[1]
                ):
                    resp += f"{part[0]}:\n\t{tag['translation']}\n"
                    found = True
            if not found:
                print("No match: ", part)
    return resp


seen = set()
if __name__ == "__main__":
    with open("/Users/kian/code/nhe-enga/anotated_results.json", "r") as f:
        data = json.load(f)
        for row in data:
            annotated = row["anotated"]
            definitions = [{"f": x[0], "d": x[1]} for x in row["definitions"]]
            if annotated in seen:
                continue
            seen.add(annotated)
            print(annotated)
            orig = clean_annotation(annotated)
            parts = parse_parts(annotated)
            classified = classify_parts_json(parts)
            roots = find_root_words(parts)
            root_defs = get_root_defs(roots, dictionary)
            print()
            prompt = generate_gpt_prompt(
                orig, classified, format_verbetes_all(definitions), "English"
            ).strip()
            print(prompt)
            print(f"The prompt is {len(prompt)} characters long")
            prompt = prompt
            # breakpoint()
            response = anthropicResponse(prompt)
            print(response)
            # save to file, appending each time to a csv file: orig, annotated, response
            with open("tupi_to_eng_anth_NEW_METHOD.csv", "a") as f:
                writer = csv.writer(f)
                for resp in response.split("\n"):
                    writer.writerow([orig, annotated, resp, prompt])
            # breakpoint()
