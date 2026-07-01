# Chalkboard-Gag Hidden Flag — Write-up

## Challenge Overview

The challenge ships a large text file (`msg_impoartant!!!!!!!!!!!!!!.txt`)
containing thousands of near-identical "chalkboard gag" lines — a phrase
repeated over and over, Simpsons-intro style — with a flag hidden by
swapping individual characters of some lines for flag characters.

```python
phrase = "a7la lila a7la ness"
flag   = "SECURINETS{FOULA_MAYTMASCH}"
```

## How It Was Built (`generate_chalkboard`)

```python
def generate_chalkboard(phrase, flag, lines=5000, filename="...", head_lines=1000):
    chalkboard_lines = []
    for _ in range(head_lines):
        chalkboard_lines.append(phrase)          # 1000 clean lines, no flag

    remaining_lines = lines - head_lines          # 4000 lines left
    flag_positions = random.sample(range(remaining_lines), len(flag))
    flag_index = 0
    for i in range(remaining_lines):
        line = list(phrase)
        if flag_index < len(flag) and i in flag_positions:
            pos = random.randint(0, len(phrase) - 1)
            line[pos] = flag[flag_index]
            flag_index += 1
        chalkboard_lines.append("".join(line))

    with open(filename, "w") as f:
        for l in chalkboard_lines:
            f.write(l + "\n")
```

Key mechanics:

- **1000 head lines** are the phrase, completely untouched — pure noise,
  no signal.
- The remaining **4000 lines** each start as a fresh copy of the phrase.
  For `len(flag) = 28` of those 4000 lines (chosen via
  `random.sample(range(remaining_lines), len(flag))`, so 28 distinct line
  indices), **one character** of the line is overwritten with the next
  character of the flag, at a **random column position** in that line.
- Crucially, `flag_positions` is a *set* of line indices, and the main loop
  walks `i` from `0` upward — so even though `random.sample` picks the 28
  positions in a random order, the loop visits them in **increasing index
  order**, and `flag_index` increments in that same order. This means
  **the flag ends up written into the file in correct order**, one
  character per selected line, top to bottom.
- Every other character on every other line is just the original phrase,
  untouched.

So the extraction task is conceptually simple: for each line, diff it
against the original phrase; any character that differs is either a flag
character (if that line was one of the 28 chosen) or nothing (if it wasn't
touched at all, since the line matches the phrase exactly).

## The Provided Solver Has a Bug

```python
phrase = "a7la lila a7la Ness"   # <-- capital "N"
...
if phrase not in clean_line:
    for i in range(min(len(phrase), len(clean_line))):
        if clean_line[i] != phrase[i]:
            all_differing_letters += clean_line[i]
```

Compare this to the generator's actual phrase:

```python
phrase = "a7la lila a7la ness"   # <-- lowercase "n"
```

The solver's copy of the phrase capitalizes the `N` in `"Ness"`, while every
line actually written to the file uses lowercase `"ness"`. Two consequences:

1. **`if phrase not in clean_line`** is checking for the *capitalized*
   phrase as a substring. Since the file only ever contains the lowercase
   version, this condition is `True` for **every single line** in the file
   — including the 1000 completely untouched head lines. The `else:
   continue` branch (meant to skip lines identical to the phrase) never
   actually fires.
2. Because *every* line gets diffed, and every line has a lowercase `n` at
   the position where the solver's phrase has an uppercase `N`, **every
   line contributes one spurious `'n'` character** to
   `all_differing_letters` — even lines that were never touched by the flag
   embedding process at all.

The net effect: running the solver as-written produces `all_differing_letters`
as a ~5000-character string that's almost entirely the noise character `n`,
with the real flag characters buried inside it — e.g. (truncated):

```
...nnnnnnnnnnSnnnnnEnnnnnnnnCnnnnnnnnU...nnnnnRnnnnnnnnnnnnnnInnn...N...E...T...S...{...F...O...U...L...A...n_nnn...M...A...Y...T...M...A...S...C...H...}nnnn...
```

## The Fix

Since the flag itself contains no lowercase `n` (it's uppercase letters,
digits/underscore/braces only), and the noise character is *always*
lowercase `n`, the flag can be recovered simply by stripping every `n` out
of the collected output:

```python
phrase = "a7la lila a7la Ness"
all_differing_letters = ""
with open("msg_impoartant!!!!!!!!!!!!!!.txt", "r") as file:
    for line in file:
        clean_line = line.strip()
        if phrase not in clean_line:
            for i in range(min(len(phrase), len(clean_line))):
                if clean_line[i] != phrase[i]:
                    all_differing_letters += clean_line[i]

flag = all_differing_letters.replace("n", "")
print("Flag:", flag)
```

This works because:

- The flag order is preserved (as established above, `flag_index`
  increments in line order), so simply concatenating all non-`n` differing
  characters, in the order encountered, reconstructs the flag correctly —
  no sorting or repositioning needed.
- The **correct** fix would instead just match the solver's `phrase`
  variable to the generator's exact casing (`"a7la lila a7la ness"`, all
  lowercase), which restores the intended behavior: only the 28 lines that
  actually contain a flag character would fail the `phrase not in
  clean_line` check, and `all_differing_letters` would already be the clean
  flag with no filtering needed. Stripping `n` after the fact is a
  work-around for the *given* (buggy) solver rather than the "proper" fix.

## Flag

```
SECURINETS{FOULA_MAYTMASCH}
```

## Notes / Caveats

- This bug is a good illustration of why **exact string/case matching**
  matters for line-diffing stego solvers — a single case mismatch in the
  reference string turns a clean signal into a mostly-noise one.
- The noise-stripping fix (`.replace("n", "")`) only works because the
  flag's alphabet happens not to overlap with the noise character. A more
  general/robust fix is to correct the `phrase` constant so it exactly
  matches what the generator wrote, rather than relying on this
  alphabet-non-overlap coincidence.
- Worth double-checking: if the head lines (1000 untouched copies of the
  phrase) had been skipped correctly by a fixed `phrase not in clean_line`
  check, the solver would run faster and produce cleaner output with no
  post-processing needed at all.
