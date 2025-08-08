from collections import Counter
import numpy as np
from tqdm import tqdm
import json, gzip

with gzip.open("../dict-conjugated.json.gz", "r") as f:
    tupi_dictionary = json.load(f)

tupi_dict_json = json.dumps(tupi_dictionary, indent=2, ensure_ascii=False)
print(f"Loaded Tupi dictionary with {len(tupi_dictionary)} entries.")


def align_strings_nw(s1, s2, pad_char="_"):
    match_score = 2
    mismatch_penalty = -1
    gap_penalty = -2

    n = len(s1)
    m = len(s2)
    score = np.zeros((n + 1, m + 1), dtype=int)

    # Initialize first row and column
    for i in range(1, n + 1):
        score[i][0] = i * gap_penalty
    for j in range(1, m + 1):
        score[0][j] = j * gap_penalty

    # Fill score matrix
    for i in tqdm(range(1, n + 1)):
        for j in range(1, m + 1):
            match = score[i - 1][j - 1] + (
                match_score if s1[i - 1] == s2[j - 1] else mismatch_penalty
            )
            delete = score[i - 1][j] + gap_penalty
            insert = score[i][j - 1] + gap_penalty
            score[i][j] = max(match, delete, insert)

    # Backtrack to build alignment
    i, j = n, m
    aligned_s1 = []
    aligned_s2 = []
    match_line = []

    while i > 0 or j > 0:
        current = score[i][j]
        if (
            i > 0
            and j > 0
            and current
            == score[i - 1][j - 1]
            + (match_score if s1[i - 1] == s2[j - 1] else mismatch_penalty)
        ):
            aligned_s1.append(s1[i - 1])
            aligned_s2.append(s2[j - 1])
            match_line.append("|" if s1[i - 1] == s2[j - 1] else " ")
            i -= 1
            j -= 1
        elif i > 0 and current == score[i - 1][j] + gap_penalty:
            aligned_s1.append(s1[i - 1])
            aligned_s2.append(pad_char)
            match_line.append(" ")
            i -= 1
        else:
            aligned_s1.append(pad_char)
            aligned_s2.append(s2[j - 1])
            match_line.append(" ")
            j -= 1

    aligned_s1 = "".join(reversed(aligned_s1))
    aligned_s2 = "".join(reversed(aligned_s2))
    match_line = "".join(reversed(match_line))

    # Find the best matching string section of length min(len(s1), len(s2))
    min_len = min(len(s1), len(s2))
    match_search = []
    match_base = []
    count = 0
    for a, b in zip(aligned_s2, aligned_s1):
        if count >= min_len:
            break
        if a != pad_char and b != pad_char:
            match_search.append(a)
            match_base.append(b)
            count += 1

    return (
        aligned_s1,
        match_line,
        aligned_s2,
        ("".join(match_search), "".join(match_base)),
    )


def align_strings(s1, s2, pad_char="_", show_match_line=True):
    len1, len2 = len(s1), len(s2)
    max_offset = len1 + len2 - 1
    best_offset = None
    best_score = -1

    for offset in tqdm(range(-len2 + 1, len1)):  # slide s2 over s1
        score = 0
        for i in range(len2):
            s1_index = offset + i
            if 0 <= s1_index < len1:
                if s1[s1_index] == s2[i]:
                    score += 1
        if score > best_score:
            best_score = score
            best_offset = offset

    # Compute the final padded strings
    if best_offset >= 0:
        pad_left = best_offset
        pad_right = max(0, (pad_left + len(s2)) - len(s1))
        s1_padded = s1 + pad_char * pad_right
        s2_padded = pad_char * pad_left + s2
    else:
        pad_left = -best_offset
        pad_right = max(0, (pad_left + len(s1)) - len(s2))
        s1_padded = pad_char * pad_left + s1
        s2_padded = s2 + pad_char * pad_right

    # Ensure both strings are the same length
    max_len = max(len(s1_padded), len(s2_padded))
    s1_padded = s1_padded.ljust(max_len, pad_char)
    s2_padded = s2_padded.ljust(max_len, pad_char)
    # Find matching portions and the size of the smaller string
    min_len = min(len(s1), len(s2))
    matches = []
    base_matches = []
    for i, (a, b) in enumerate(zip(s1_padded, s2_padded)):
        if i >= min_len:
            break
        if a == b and a != pad_char:
            matches.append(b)
            base_matches.append(a)
        else:
            matches.append(pad_char)
            base_matches.append(a if a != pad_char else pad_char)
    match_str = "".join(matches)
    base_match_str = "".join(base_matches)

    if show_match_line:
        match_line = "".join(
            "|" if a == b else " "
            for a, b in zip(s1_padded[:min_len], s2_padded[:min_len])
        )
        return (s1_padded, match_line, s2_padded, (match_str, base_match_str))
    else:
        return (s1_padded, s2_padded, (match_str, base_match_str))


def filter_dict(dictionary, target):
    # for each word in target, at to a set the rows which contain the word in 'f' or 'd'
    rows = set()
    for word in target.split():
        for i, entry in enumerate(dictionary):
            if word in entry["f"] or word in entry["d"]:
                rows.add((entry["f"], entry["d"]))
    # return the filtered dictionary as a string
    return list(rows)


if __name__ == "__main__":
    target = "ra'angaba"
    # a, b, m = align_strings(base, target, show_match_line=True)
    # print(a)
    # print(b)
    # print(m)
    base = filter_dict(tupi_dictionary, target)
    a, b, m, match = align_strings(
        "\n".join([entry["f"] + f" ({entry['d']})" for entry in tupi_dictionary]),
        target,
    )
    print(a.replace("-", "").strip("-"))
    print(b)
    print(m.replace("-", "").strip("-"))
    print(match[0].replace("-", "").strip())
    print(match[1].replace("-", "").strip())
    print([x for x in base if match[1] in x[0] or match[1] in x[1]])
