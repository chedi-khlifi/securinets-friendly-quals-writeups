# Securinets CTF — "Quantum Go BRRR" (BB84) Writeup

## Challenge

We're given a `challenge/` folder containing:

- `ryuma_bases.txt` — a string of `+`/`x` characters
- `foula_bases.txt` — a string of `+`/`x` characters
- `foula_bits.txt` — a string of `0`/`1` characters
- `message_enc.bin` — raw encrypted bytes

All three text files are the same length, and their names strongly hint at
**BB84**, the quantum key distribution protocol: two parties ("Ryuma" and
"Foula" here, standing in for the usual Alice/Bob) each pick random
*bases* to encode/measure qubits in. Only when both parties happened to
pick the **same basis** for a given qubit is the resulting bit guaranteed
to match and usable as key material — this basis-matching step is called
**sifting**.

## Analysis

In real BB84:

- The sender encodes random bits in randomly chosen bases (`+` = rectilinear, `x` = diagonal).
- The receiver measures each qubit in an independently chosen random basis.
- When sender and receiver's bases **agree**, the receiver's measured bit
  reliably matches the sender's original bit.
- When the bases **disagree**, the measurement result is essentially random
  noise (unusable).
- Afterward, both sides publicly compare (only) their basis choices — never
  the bits — over a classical channel, throw away all positions where the
  bases didn't match, and keep the rest. This surviving subset is the
  **sifted key**.

Here we're given exactly the classical-channel artifacts of that process:
`ryuma_bases.txt` (sender's bases) and `foula_bases.txt` (receiver's bases)
let us figure out *which positions* were kept, and `foula_bits.txt` (the
receiver's measured bits) gives us the actual bit values at every
position — including the "wasted" mismatched ones, which we simply ignore.

Once we've reconstructed the sifted key bits, we pack them into bytes and
use that as a repeating-key XOR stream to decrypt `message_enc.bin` — the
classic "one-time-pad-style" symmetric encryption you'd expect at the end
of a QKD protocol demo.

## Solving

Steps:

1. Read all three basis/bit files plus the ciphertext.
2. Sanity check that the three text files have matching lengths (each
   position corresponds to one transmitted qubit).
3. Sift: keep the bit from `foula_bits.txt` at every index `i` where
   `ryuma_bases[i] == foula_bases[i]`.
4. Concatenate the surviving bits into one binary string, zero-pad it out
   to a multiple of 8 bits, and pack it into bytes to get the recovered key.
5. Repeat/tile the key to match the ciphertext length, and XOR it against
   `message_enc.bin` byte-by-byte to recover the plaintext.

```python
from pathlib import Path

C = Path("challenge")
ryuma_bases = C.joinpath("ryuma_bases.txt").read_text().strip()
foula_bases = C.joinpath("foula_bases.txt").read_text().strip()
foula_bits  = C.joinpath("foula_bits.txt").read_text().strip()
ct = C.joinpath("message_enc.bin").read_bytes()

# Sifting: keep bits only where both parties' bases matched
sifted_bits = ''.join(
    foula_bits[i] for i in range(len(ryuma_bases))
    if ryuma_bases[i] == foula_bases[i]
)

# Pack sifted bits into bytes (the recovered symmetric key)
pad = (-len(sifted_bits)) % 8
s_padded = sifted_bits + ("0" * pad)
key_bytes = bytes(int(s_padded[i:i+8], 2) for i in range(0, len(s_padded), 8))

# Repeating-key XOR decryption
rep_key = (key_bytes * ((len(ct) // len(key_bytes)) + 1))[:len(ct)]
pt = bytes(a ^ b for a, b in zip(ct, rep_key))

print(pt.decode(errors="replace"))
```

### Why this works

- Sifting is deterministic and public information (bases are compared
  openly in BB84) — so anyone holding all three files can redo it exactly
  the same way the legitimate protocol participants would.
- Only the *bits* at matching-basis positions are trustworthy; mismatched
  positions are correctly discarded rather than corrupting the key.
- Packing bits MSB-first into bytes, 8 at a time, is the natural way to
  turn a raw bitstring into a usable byte key (with zero-padding on any
  leftover partial byte at the end).
- The final XOR step just reverses the repeating-key XOR encryption that
  was applied to the flag using this same sifted key.

## Result

Running the solve script against a generated challenge instance:

```
Sifted key length (bits): 271
Sifted key length (bytes): 34
Sifted key (hex): 397980ba0791dcd14eede7a3678d9f6c851f4055c05bdb6a2f4881d0166bbadf16c6

Decrypted plaintext (raw):
Securinets{Quantum_go_BRRRRRRRRRRRRRRRRRRRRRRRR}
```

**Flag format:** `Securinets{...}` (recovered directly from the decrypted
plaintext — no brute forcing needed once the key is correctly sifted).

## Takeaways

- Filenames referencing two parties' "bases" and "bits" alongside an
  encrypted message are a strong signal for a **BB84-style QKD**
  challenge — the core task is reconstructing the *sifted key*, not
  breaking any cryptography by force.
- Sifting is just a filter: keep bit `i` only where both basis strings
  agree at position `i`.
- Once you have the shared key, the rest is a standard repeating-key XOR
  decryption — the "quantum" part of the challenge is entirely about
  correctly deriving the key, not about the symmetric cipher itself.
