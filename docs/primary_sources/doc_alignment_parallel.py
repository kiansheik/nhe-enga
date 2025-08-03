import numpy as np
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import json, gzip

with gzip.open('../dict-conjugated.json.gz', 'r') as f:
    tupi_dictionary = json.load(f)
tupi_dict_json = json.dumps(tupi_dictionary, ensure_ascii=False)

def align_strings_nw(s1, s2, pad_char='_'):
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

    def process_diagonal(k):
        # Process anti-diagonal with index k = i + j
        tasks = []
        for i in range(max(1, k - m), min(n, k) + 1):
            j = k - i
            if j < 1 or j > m:
                continue
            match = score[i - 1][j - 1] + (match_score if s1[i - 1] == s2[j - 1] else mismatch_penalty)
            delete = score[i - 1][j] + gap_penalty
            insert = score[i][j - 1] + gap_penalty
            tasks.append((i, j, max(match, delete, insert)))
        return tasks

    # Fill score matrix in parallel by diagonals
    for k in tqdm(range(2, n + m + 1)):  # Start at 2 to skip (0,0), (1,0), (0,1)
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda args: args, process_diagonal(k)))
        for i, j, val in results:
            score[i][j] = val

    # Backtrack to build alignment
    i, j = n, m
    aligned_s1 = []
    aligned_s2 = []
    match_line = []

    while i > 0 or j > 0:
        current = score[i][j]
        if i > 0 and j > 0 and current == score[i - 1][j - 1] + (match_score if s1[i - 1] == s2[j - 1] else mismatch_penalty):
            aligned_s1.append(s1[i - 1])
            aligned_s2.append(s2[j - 1])
            match_line.append('|' if s1[i - 1] == s2[j - 1] else ' ')
            i -= 1
            j -= 1
        elif i > 0 and current == score[i - 1][j] + gap_penalty:
            aligned_s1.append(s1[i - 1])
            aligned_s2.append(pad_char)
            match_line.append(' ')
            i -= 1
        else:
            aligned_s1.append(pad_char)
            aligned_s2.append(s2[j - 1])
            match_line.append(' ')
            j -= 1

    aligned_s1 = ''.join(reversed(aligned_s1))
    aligned_s2 = ''.join(reversed(aligned_s2))
    match_line = ''.join(reversed(match_line))

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
        (''.join(match_search), ''.join(match_base))
    )

if __name__ == "__main__":
    target = tupi_dict_json
    base = "Santa Cruz ra'angaba resé oré pysyrõ îepé, Tupã oré îar, oreamotare'ymbara suí. Tuba"
    # a, b, m = align_strings(base, target, show_match_line=True)
    # print(a)
    # print(b)
    # print(m)
    a, b, m, matching_search, matching_base = align_strings_nw(base, target,)
    print(a)
    print(b)
    print(m)
    print(matching_base)    
    print(matching_search)