
phrase = "a7la lila a7la Ness"


all_differing_letters = ""

with open("msg_impoartant!!!!!!!!!!!!!!.txt", "r") as file:
    for line in file:
        clean_line = line.strip()
        if phrase not in clean_line:

            for i in range(min(len(phrase), len(clean_line))):
                if clean_line[i] != phrase[i]:
                    all_differing_letters += clean_line[i]
        else:
            continue
print("All differing letters:", all_differing_letters)