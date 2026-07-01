from PIL import Image
import hashlib, random, os

def seed_from_password(password: str) -> int:
    return int(hashlib.sha256(password.encode()).hexdigest(), 16)

def unshuffle_and_xor(in_path, out_path, password):
    """Reverse the XOR + shuffle process deterministically."""
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
    print(f"[+] Restored original image to {out_path}")

def main():
    print("=== XOR + Unshuffle Image Solver ===")
    img_path = input("Enter encrypted image path: ").strip()
    if not os.path.isfile(img_path):
        print("[!] File not found.")
        return

    password = input("Enter password: ").strip()
    if not password:
        print("[!] No password provided.")
        return

    base, _ = os.path.splitext(img_path)
    out_path = base + "_restored.png"
    unshuffle_and_xor(img_path, out_path, password)

if __name__ == "__main__":
    main()
