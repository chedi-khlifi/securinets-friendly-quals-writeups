# XOR + Shuffle Image Challenge — Write-up

## Challenge Overview

The challenge provides `task.py`, a tool that "encrypts" a PNG image using a
password-derived deterministic transform. Given the encrypted output image
and the correct password, the goal is to recover the original image.

The transform in `task.py` does two things, in this order:

1. **XOR each pixel's R, G, B channels** with a stream of pseudo-random bytes
   generated from a `random.Random` instance seeded by the password.
2. **Shuffle the pixel order** using `random.shuffle()` on the *same* RNG
   instance, re-seeded with the same seed.

```python
def seed_from_password(password: str) -> int:
    return int(hashlib.sha256(password.encode()).hexdigest(), 16)
```

The password is hashed with SHA-256 and the resulting hex digest is
converted to a big integer, which seeds Python's Mersenne Twister
(`random.Random`). Because `random.Random` is fully deterministic given a
seed, anyone who knows the password can reproduce the *exact same* sequence
of pseudo-random numbers — which is what makes this reversible without
needing to "crack" anything, as long as the password is known.

## Why It's Reversible

Both the XOR step and the shuffle step are **self-inverse operations** when
you know the exact keystream/permutation used:

- XOR is its own inverse: `(p XOR k) XOR k == p`.
- A shuffle defined by a permutation array `indices` can be undone by
  placing each element back at its original index: if
  `shuffled[i] = data[indices[i]]`, then `data[indices[i]] = shuffled[i]`
  restores the original array.

The only catch is **order of operations**. `task.py` does:

```
original --XOR--> xored --shuffle--> shuffled (final output)
```

So to reverse it, you must **undo the steps in the opposite order**:

```
shuffled --unshuffle--> xored --XOR--> original
```

That is exactly what `solver.py` does:

```python
def unshuffle_and_xor(in_path, out_path, password):
    img = Image.open(in_path).convert("RGBA")
    w, h = img.size
    data = list(img.getdata())  # shuffled + XORed pixels

    # Recreate same shuffle order
    seed = seed_from_password(password)
    rng = random.Random(seed)
    indices = list(range(len(data)))
    rng.shuffle(indices)

    # === 1. Unshuffle ===
    unshuffled = [None] * len(data)
    for i, shuffled_index in enumerate(indices):
        unshuffled[shuffled_index] = data[i]

    # === 2. Reverse XOR ===
    rng = random.Random(seed)
    original_pixels = []
    for (r, g, b, a) in unshuffled:
        r ^= rng.randrange(256)
        g ^= rng.randrange(256)
        b ^= rng.randrange(256)
        original_pixels.append((r, g, b, a))

    out_img = Image.new("RGBA", (w, h))
    out_img.putdata(original_pixels)
    out_img.save(out_path, "PNG")
```

Key points:

- `rng.shuffle(indices)` on a **fresh** `list(range(len(data)))` reproduces
  the exact permutation used by `task.py`, because both scripts seed with
  the same `seed_from_password(password)` value.
- The RNG is **reset** (`rng = random.Random(seed)`) before the unshuffle
  and again before the XOR reversal — mirroring `task.py`, which also
  re-seeds (`rng = random.Random(seed)`) right before the shuffle step so
  that the XOR keystream and the shuffle permutation are generated
  independently from the same seed, each starting fresh.
- `unshuffled[shuffled_index] = data[i]` is the correct inverse mapping:
  since the forward step was `shuffled[i] = new_pixels[indices[i]]`,
  solving for `new_pixels[indices[i]]` gives back the pre-shuffle order.
- The alpha channel (`a`) is left untouched, matching the original script
  (only R, G, B are XORed).

## Usage

```bash
pip install pillow
python3 solver.py
```

The script will prompt for:

1. **Encrypted image path** — the `_xor_shuffle.png` file produced by
   `task.py`.
2. **Password** — the same password originally used to encrypt it.

It outputs `<original_name>_restored.png` in the same directory, which
should match the original image exactly (assuming the correct password was
used and the image wasn't re-compressed/re-saved in a lossy format between
runs).

## Notes / Caveats

- This scheme relies entirely on the password remaining secret — the
  "encryption" itself is just a keystream XOR plus a keyed permutation, both
  derived from `random.Random`, which is **not cryptographically secure**
  (it's a Mersenne Twister, not a CSPRNG). In a real security context this
  would be brute-forceable or predictable from partial output, but for a
  CTF-style reversible puzzle where the password is required input, it
  works as intended.
- Correctness depends on pixel *count* and *order* being preserved between
  encryption and decryption — the image must not have been resized,
  re-encoded lossily, or had its pixel data reordered by any other tool in
  between.
