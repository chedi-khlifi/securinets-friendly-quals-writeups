import random

def generate_chalkboard(phrase, flag, lines=5000, filename="msg_impoartant!!!!!!!!!!!!!!.txt", head_lines=1000):
    """
    Generates a chalkboard gag text file where the flag is hidden by
    modifying letters in the repeated phrase.
    
    :param phrase: The repeated phrase (string)
    :param flag: The flag you want to hide (string)
    :param lines: Total number of lines in the file (including head_lines)
    :param filename: Output file name
    :param head_lines: Number of lines at the start without flag
    """
    chalkboard_lines = []

    # Add head lines with no flag
    for _ in range(head_lines):
        chalkboard_lines.append(phrase)

    # Generate remaining lines with flag characters randomly distributed
    remaining_lines = lines - head_lines
    flag_positions = random.sample(range(remaining_lines), len(flag))  # lines to hide each flag char
    flag_index = 0

    for i in range(remaining_lines):
        line = list(phrase)
        if flag_index < len(flag) and i in flag_positions:
            # Random position in the line to hide flag character
            pos = random.randint(0, len(phrase) - 1)
            line[pos] = flag[flag_index]
            flag_index += 1
        chalkboard_lines.append("".join(line))
    
    # Write to file
    with open(filename, "w") as f:
        for l in chalkboard_lines:
            f.write(l + "\n")
    
    print(f"[+] Chalkboard gag file '{filename}' generated with hidden flag!")

# Example usage
phrase = "a7la lila a7la ness"

flag = "SECURINETS{FOULA_MAYTMASCH}"
generate_chalkboard(phrase, flag)
