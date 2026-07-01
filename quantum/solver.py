#!/usr/bin/env python3
from pathlib import Path

C = Path("challenge")
ryuma_bases = C.joinpath("ryuma_bases.txt").read_text().strip()
foula_bases = C.joinpath("foula_bases.txt").read_text().strip()
foula_bits = C.joinpath("foula_bits.txt").read_text().strip()
ct = C.joinpath("message_enc.bin").read_bytes()

if not (len(ryuma_bases) == len(foula_bases) == len(foula_bits)):
    raise SystemExit("Input files lengths mismatch.")

sifted_bits_list = [foula_bits[i] for i in range(len(ryuma_bases)) if ryuma_bases[i] == foula_bases[i]]
sifted_bits = ''.join(sifted_bits_list)

if len(sifted_bits) == 0:
    raise SystemExit("No sifted bits found (sifted key empty)")

pad = (-len(sifted_bits)) % 8
s_padded = sifted_bits + ("0" * pad)
key_bytes = bytes(int(s_padded[i:i+8], 2) for i in range(0, len(s_padded), 8))

C.joinpath("recovered_key.bin").write_bytes(key_bytes)

print("Sifted key (bits):", sifted_bits)
print("Sifted key length (bits):", len(sifted_bits))
print("Sifted key length (bytes):", len(key_bytes))
print("Sifted key (hex):", key_bytes.hex())
try:
    text = key_bytes.decode('utf-8')
    print("Sifted key (utf-8):", text)
except Exception:
    print("Sifted key (utf-8): (not valid UTF-8)")

rep_key = (key_bytes * ((len(ct) // len(key_bytes)) + 1))[:len(ct)]
pt = bytes(a ^ b for a, b in zip(ct, rep_key))

print("\nDecrypted plaintext (raw):")
print(pt.decode(errors="replace"))
