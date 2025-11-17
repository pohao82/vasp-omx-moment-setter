def find_start_by_char_transition(line, target_token_number=6):
    """
    Helper function implementing the transition-counting logic to find the
    starting index of the Nth token (where N=6 for M_init).
    """
    current_transition = 0
    in_token = False

    for i, char in enumerate(line):
        is_space = char.isspace()

        if not is_space:
            in_token = True
        elif is_space and in_token:
            # Transition: non-space to space (end of a token)
            current_transition += 1
            in_token = False

            # If we've hit the end of the (N-1)th token
            if current_transition == target_token_number - 1:
                # Find the first non-space character of the Nth token (M_init)
                start_of_next_token = i 
                return i
                #while start_of_next_token < len(line) and line[start_of_next_token].isspace():
                #    start_of_next_token += 1
                #return start_of_next_token

    return -1


def parse_selection_string(selection_str, max_index):
    """Parses a string like '1, 3:6, 9' into a list of indices."""
    if not selection_str:
        return []

    indices = set()
    parts = selection_str.replace(" ", "").split(',')

    for part in parts:
        if not part:
            continue
        if ':' in part:
            start, end = part.split(':')
            start, end = int(start), int(end)
            if start > end:
                raise ValueError(f"Invalid range: {start}:{end}")
            for i in range(start, end + 1):
                if 0 <= i <= max_index:
                    indices.add(i)
        else:
            idx = int(part)
            if 0 <= idx <= max_index:
                indices.add(idx)

    return sorted(list(indices))

## Example string to find the start of the M_init (6th token)
##line = '20  Se  0.57344997  0.92654997  0.20619994  7.5  5.5  90.00...'
#line = '16	Se	0.92654997	0.57344997	0.79380000	2.5	3.5	180.0	0.0	180.0	0.0'
#parts = line.split()
#print(line)
#
#start_index = find_start_by_char_transition(line, 6) 
#print(start_index)
#print(line[:start_index])
# start_index will be the exact index of '7' in '7.5'
