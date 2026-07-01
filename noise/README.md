# Securinets CTF — "Noisy XOR" Writeup

## Challenge

We're given a single file, `chall.txt`, containing one long Base64-encoded
string. No other hints are provided about how it was generated.

```
WDJoDskDLPIQ52MwMUBBQFJUY85sYgA1yplgofFRGIYbnmXoptfBbwJAmRFi9cFtj3xfxSfcEqB4Sq1dQ...
```

## Analysis

Decoding the Base64 gives a stream of raw bytes that look like noise —
no obvious ASCII, no printable structure. That pattern (Base64 wrapping
opaque binary data) is a strong hint that a simple reversible transform,
most likely a XOR cipher, was applied before encoding.

Since the ciphertext shows no repeating block structure and there's only
one key hinted at, the natural guess is a **single-byte XOR key** applied
to every byte of the payload. A single-byte XOR key has only 256 possible
values, so it's trivially brute-forceable — we just try every key from
`0` to `255` and check whether the result contains a recognizable flag
prefix.

The target CTF's flag format is `Securintes{...}`, so the check is simple:
does the decoded byte string contain `b"Securintes{"`?

## Solving

Steps:

1. Read and Base64-decode `chall.txt` to get the raw ciphertext bytes.
2. Loop over all 256 possible single-byte XOR keys.
3. For each key, XOR every byte of the ciphertext with that key.
4. Check if the decoded result contains the marker `Securintes{`.
5. Once found, print the key and decode the bytes as `latin1` (to avoid
   crashing on any leftover noise bytes that aren't valid UTF-8).

```python
import base64

with open("chall.txt", "r") as f:
    b64 = f.read().strip()

data = base64.b64decode(b64)

for key in range(256):
    decoded = bytes(b ^ key for b in data)
    if b"Securintes{" in decoded:
        print("Found key:", key)
        print("Decoded text:")
        print(decoded.decode("latin1"))
        break
else:
    print("Flag not found.")
```

### Why this works

- Base64 decoding recovers the exact byte stream that was XORed.
- XOR is its own inverse: `(byte ^ key) ^ key == byte`. So XOR-ing the
  ciphertext with the *correct* key restores the original plaintext bytes.
- Because there's only one byte of keyspace (256 possibilities), brute
  force is instant — no need for frequency analysis or smarter
  cryptanalysis.
- A large chunk of the decoded output is meaningless noise bytes (garbage
  prepended before the flag), but that doesn't matter: as soon as the
  correct key is tried, the readable flag string appears intact at the
  end of the decoded buffer, and the `Securintes{` substring check picks
  it out reliably even amid the noise.

## Result

Running the solver:

```
Found key: 174
...
Securintes{Sou5riette_All_9adar_Ya_Karim}
```

**Flag:** `Securintes{Sou5riette_All_9adar_Ya_Karim}`

## Takeaways

- Base64 wrapping "random-looking" binary data is a classic tell for an
  underlying XOR (or other reversible byte-level) cipher.
- Single-byte XOR is always worth brute-forcing first — the keyspace is
  tiny (256 values) and a known-plaintext marker (like a flag prefix)
  makes automatic detection trivial.
- Junk/noise padding around the real data doesn't defeat this approach;
  substring search for a known format is robust to leading garbage.
