# Flag Coordinates Plot — Analysis (corrected against source)

## Correction vs. the earlier report

The first version of this write-up guessed the mechanism from the chart alone and described it as a genetic algorithm with "generations." Having now seen `flag_coordinates_plot.py`, that's wrong — there's no population, mutation, or selection across generations. What's actually happening is a **positional brute-force / hill-climbing oracle attack**: a byte-at-a-time style recovery of a static secret string using a "number of characters matched" oracle, one position at a time.

## What the script does

```
for each position i in the target string:
    for each candidate character c in the alphabet:
        try c at position i (keep every other position at its best-known value so far)
        score = count of positions where guess == target
        keep track of the best-scoring c for this position
    lock in the best character found for position i
```

This is a classic **coordinate-ascent** approach: instead of searching the full keyspace (`len(alphabet) ^ len(flag)`, astronomically large), it exploits an oracle that reveals a similarity score, and solves each character position independently and sequentially, in linear time.

## Configuration (from source)

| Parameter | Value |
|---|---|
| Alphabet | `a-z`, `A-Z`, `0-9`, `{`, `}`, `_` |
| Alphabet size | 65 characters |
| Target flag | `Securintes{0nC3_BssIsa_4lw4yS_BsiSSa}` |
| Flag length | 37 characters |
| Total oracle queries | 65 × 37 = **2,405** (matches the plot's 2,405 attempts exactly) |
| Initial guess | `'a'` repeated 37 times |

This is why the plot showed dashed red separators every 65 attempts — each block of 65 is one full alphabet sweep for a single position, not a "generation" of a GA.

## Result

Running the script recovers the flag **exactly**, matching the hardcoded target:

```
Final guessed flag: Securintes{0nC3_BssIsa_4lw4yS_BsiSSa}
Match: True
```

The y-axis climb seen in the chart (9 → 37 matched letters) is simply the running match-count as each position gets locked to its correct character, one sweep of 65 candidates at a time. It rises almost monotonically because early positions in the string already coincidentally match the initial `'a'` guess (accounting for the starting value of 9), and each subsequent position-sweep either finds and locks the correct character (raising the total match count by 1) or, if the correct character happens to already be `'a'` or another already-matching filler, contributes no visible jump.

## Complexity

- **Brute force over full string:** `65^37` guesses — computationally infeasible.
- **This oracle-guided, position-by-position approach:** `65 × 37 = 2,405` guesses — trivial, runs in milliseconds.

This efficiency gain is the entire point of the technique: it only works because the oracle leaks a *partial* score (count of matching characters) rather than an all-or-nothing pass/fail, which is what makes character-by-character recovery possible. This is the same principle behind timing side-channel and byte-at-a-time oracle attacks seen in CTF pwn/crypto challenges.

## Note on consecutive-mismatch detection

The script also cross-checks `ref` (guessed flag) against the real flag for consecutive wrong positions, as a sanity/debug step — in this run there are none, since the guessed flag matches perfectly.

## Files

- `flag_coordinates_plot.py` — the recovery + plotting script
- `plot_flag.html` — the Plotly chart of match-count progress across all 2,405 queries
