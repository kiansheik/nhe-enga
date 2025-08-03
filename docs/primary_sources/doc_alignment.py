def align_strings(s1, s2, pad_char='_', show_match_line=False):
    if len(s1) >= len(s2):
        base_string = s1
        search_string = s2
    else:
        base_string = s2
        search_string = s1

    full_search_len = len(base_string) + len(search_string) - 1 # starting on overlap
    match_line = ''
    for i in range(full_search_len):
        # Calculate the start and end indices for the current alignment window
        start = max(0, i - len(search_string) + 1)
        end = min(len(base_string), i + 1)

        # Extract the current alignment window
        base_window = base_string[start:end]
        search_window = search_string[start:end]

        # Check for matches in the current alignment window
        if base_window == search_window:
            # If a match is found, pad the strings and return the result
            base_string = base_string.ljust(len(search_string), pad_char)
            search_string = search_string.ljust(len(base_string), pad_char)
            if not show_match_line:
                return (base_string, search_string)

            match_line = ''.join(
                '|' if a == b and a != pad_char else ' '
                for a, b in zip(base_string, search_string)
            )
    return (base_string, search_string, match_line)


if __name__ == "__main__":
    a, b, m = align_strings("abcde", "cdefg", show_match_line=True)
    print(a)
    print(b)
    print(m)