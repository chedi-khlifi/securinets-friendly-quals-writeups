from PIL import Image
import hashlib, random, os

def seed_from_password(password: str) -> int:
    """Create an integer seed from password."""
    return int(hashlib.sha256(password.encode()).hexdigest(), 16)

def xor_and_shuffle(in_path, out_path, password):
    """XOR + shuffle pixel order deterministically using password."""
    img = Image.open(in_path).convert("RGBA")
    w, h = img.size
    data = list(img.getdata())  # [(r,g,b,a), ...]

    # Create RNG seeded by password
    seed = seed_from_password(password)
    rng = random.Random(seed)

    # === 1. XOR pixel colors ===
    new_pixels = []
    for (r, g, b, a) in data:
        r ^= rng.randrange(256)
        g ^= rng.randrange(256)
        b ^= rng.randrange(256)
        new_pixels.append((r, g, b, a))

    # === 2. Shuffle pixel order ===
    indices = list(range(len(new_pixels)))
    rng = random.Random(seed)  # reset RNG so both encode/decode symmetric
    rng.shuffle(indices)

    shuffled = [new_pixels[i] for i in indices]

    out_img = Image.new("RGBA", (w, h))
    out_img.putdata(shuffled)
    out_img.save(out_path, "PNG")
    print(f"[+] Saved XOR+shuffled image to {out_path}")

def main():
    print("=== XOR + Shuffle Image Tool ===")
    img_path = input("Enter image path: ").strip()
    if not os.path.isfile(img_path):
        print("[!] File not found.")
        return

    password = input("Enter password: ").strip()
    if not password:
        print("[!] No password provided.")
        return

    base, _ = os.path.splitext(img_path)
    out_path = base + "_xor_shuffle.png"
    xor_and_shuffle(img_path, out_path, password)
    print("[*] Done. Run again with the same password to restore the original image.")

if __name__ == "__main__":
    main()
