# solver.py — simple and direct
import base64

# read Base64 string from chall.txt
with open("chall.txt", "r") as f:
    b64 = f.read().strip()

# decode Base64
data = base64.b64decode(b64)

# brute-force single-byte XOR
for key in range(256):
    decoded = bytes(b ^ key for b in data)
    if b"Securintes{" in decoded:
        print("Found key:", key)
        print("Decoded text:")
        print(decoded.decode("latin1"))  # latin1 avoids decode errors
        break
else:
    print("Flag not found.")
