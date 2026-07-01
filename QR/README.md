# CTF QR Code GIF Challenge — Write-up

## Challenge Overview

The challenge ships an animated GIF (`qr_animation.gif`) built by `setup.py`.
The setup script generates **8 colored QR codes**, each encoding a different
string (a message, a base64 fragment, or a URL). Each QR code is then sliced
into **4 horizontal strips**, and all `8 × 4 = 32` strip images are stitched
together — in order — into a single animated GIF, one strip per frame.

The goal is to reverse this process: pull every frame back out of the GIF,
regroup them into sets of 4, stack each set back into a full QR code image,
and decode each QR to recover the original 8 strings — one of which is the
flag (split across two of the QR codes as base64).

## How the Challenge Is Built (`setup.py`)

```python
words = [
    "per aspera ad astra",
    "jelas kamu sangat membutuhkan informasi",
    "U2VjdXJpbmV0c3tLaW1hXzlhbF9jaG9j",
    "https://pastebin.com/HQBF32MU",
    "b19rYWxsZWxfcmFob3VfdGZvdWxfYmVoaX0=",
    "https://www.chess.com/forum/view/fun-with-chess/gold-coins-game",
    "https://youtu.be/fB32nZLzM-w?si=zVRf7mqEhpeDJsuE",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=RDdQw4w9WgXcQ&start_radio=1",
]
```

Key mechanics:

1. **QR generation** — each string becomes a QR code (`qrcode` library) in a
   distinct fill color, high error-correction level, rendered onto a fixed
   `400×400` white canvas so every QR image is identically sized regardless
   of the original QR "version" needed for that string's length.
2. **Splitting** — each `400×400` QR is cut into 4 horizontal strips of
   `100px` height each (`split_qr_codes`), saved as `{qr_num}_part_{part}.png`.
3. **GIF assembly** — `create_animated_gif` walks QR 1 → QR 8, and for each,
   appends its 4 parts *in order* (`part_0, part_1, part_2, part_3`) as
   consecutive GIF frames. The final GIF therefore has frames laid out as:

   ```
   [QR1_p0, QR1_p1, QR1_p2, QR1_p3, QR2_p0, QR2_p1, ... QR8_p3]
   ```

   i.e. **every 4 consecutive frames belong to one QR code**, and within
   that group the frames are already in top-to-bottom order.
4. Temp files (individual QR PNGs and parts) are deleted, leaving only the
   GIF — the reversal has to work purely from the GIF's frames.

Note the console output at the end of `setup.py` prints a flag string
(`Securinets{1C4M3154W1C0nQRu3r3D}`), but that's just a placeholder/log line
in the script — it does **not** correspond to the actual encoded content.
The real flag is only recoverable by decoding the QR codes themselves (see
[Flag Analysis](#flag-analysis) below).

## How the Solver Works (`solver.py`)

The solve script mirrors the build process in reverse:

### 1. Extract every frame from the GIF

```python
def extract_frames_from_gif(gif_path, output_dir="frames"):
    gif = Image.open(gif_path)
    frame_count = 0
    try:
        while True:
            frame = gif.copy()
            frame.save(f"{output_dir}/frame_{frame_count:03d}.png")
            frame_count += 1
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
```

Pillow's animated-image API doesn't expose "all frames" directly — you have
to `seek()` through them one at a time until it raises `EOFError` at the
end. Each frame is saved as its own PNG (`frame_000.png`, `frame_001.png`,
...), preserving the original GIF order.

### 2. Regroup frames into QR-sized batches

```python
def group_frames_by_qr(frame_dir, parts_per_qr=4):
    frames = sorted([f for f in os.listdir(frame_dir) if f.endswith('.png')])
    total_qrs = len(frames) // parts_per_qr
    ...
```

Since the builder always emits exactly 4 frames per QR code, in order, the
inverse is trivial: sort the extracted frame filenames (zero-padded, so
lexicographic sort == numeric sort) and chop the list into consecutive
chunks of 4. Chunk `i` = QR code `i`'s four strips, still top-to-bottom.

### 3. Reconstruct each QR code by vertical stacking

```python
def reconstruct_qr(frame_paths, frame_dir, output_path):
    parts = [Image.open(os.path.join(frame_dir, f)) for f in frame_paths]
    width = parts[0].width
    total_height = sum(part.height for part in parts)
    reconstructed = Image.new('RGB', (width, total_height))
    y_offset = 0
    for part in parts:
        reconstructed.paste(part, (0, y_offset))
        y_offset += part.height
    reconstructed.save(output_path)
```

This is the exact inverse of the splitting step: strips were cut by taking
horizontal bands top-to-bottom, so pasting them back top-to-bottom at
increasing `y_offset` restores the full `400×400` (or thereabouts) QR image.

### 4. Decode each reconstructed QR

```python
def decode_qr(image_path):
    img = cv2.imread(image_path)
    decoded_objects = decode(img)          # pyzbar, via OpenCV load
    if decoded_objects:
        return decoded_objects[0].data.decode('utf-8')
    else:
        pil_img = Image.open(image_path)   # fallback: load via PIL instead
        decoded_objects = decode(pil_img)
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
    return None
```

`pyzbar.decode()` is tried first against an OpenCV (`cv2.imread`) array,
then — as a fallback in case OpenCV's color/format handling trips up the
scanner — against a PIL-loaded image instead. This resilience matters
because the QR codes are colored (not plain black/white), which can
occasionally affect binarization depending on how the image is loaded.

### 5. Flag extraction heuristic

```python
base64_parts = []
for qr_num, content in results:
    if content and not content.startswith('http'):
        if any(c in content for c in ['=', 'A-Za-z0-9']):
            base64_parts.append(content)

combined = ''.join(base64_parts)
decoded_flag = base64.b64decode(combined).decode('utf-8')
```

The solver filters out anything starting with `http` (the decoy URL QR
codes) and treats the rest as candidate base64 fragments, concatenating them
in QR order and attempting a single `base64.b64decode`. This works here
because the challenge author deliberately split one base64 string across two
separate QR codes — decoding only works once both halves are joined in the
right order.

> **Note:** the filter condition `any(c in content for c in ['=', 'A-Za-z0-9'])`
> is a bit loose (it checks for the literal substring `'A-Za-z0-9'`, which
> will never match real content, so in practice this branch only fires
> because of the `'='` check or is otherwise permissive). It happens to work
> for this specific challenge layout but isn't a rigorous base64 detector —
> worth tightening with a regex like `^[A-Za-z0-9+/]+=*$` if reusing this
> solver elsewhere.

## Flag Analysis

Two of the 8 QR codes decode to base64 fragments:

| QR # | Decoded content |
|------|------------------|
| 3 | `U2VjdXJpbmV0c3tLaW1hXzlhbF9jaG9j` |
| 5 | `b19rYWxsZWxfcmFob3VfdGZvdWxfYmVoaX0=` |

Concatenated in order (`QR3 + QR5`) and base64-decoded:

```
Securinets{Kima_9al_choco_kallel_rahou_tfoul_behi}
```

This is the real flag — a Tunisian-dialect phrase encoded as the challenge
answer. It differs from the placeholder string `setup.py` prints to its own
console (`Securinets{1C4M3154W1C0nQRu3r3D}`), which is just leftover/example
text and not derived from the actual QR payloads.

The other 6 QR codes are decoys:

- Two plain-text phrases (Latin and Indonesian) — flavor text, not part of
  the flag.
- Three YouTube/Chess.com/Pastebin URLs — rabbit holes; visiting them
  doesn't yield anything challenge-relevant (one is a rickroll).

## Usage

```bash
pip install pillow opencv-python pyzbar
# pyzbar also requires the system zbar library:
#   Debian/Ubuntu: sudo apt-get install libzbar0
#   macOS:         brew install zbar

python3 solver.py qr_animation.gif
```

Output includes per-QR decoded content, a summary table, and the final
base64-decoded flag if the concatenation succeeds.

## Notes / Caveats

- The solver assumes a fixed **4 parts per QR** and that frames appear in
  the GIF in strict build order — it does no content-based matching, so if
  frames were ever shuffled or the GIF re-encoded with reordering, this
  approach would need to inspect the reconstructed images rather than trust
  positional grouping.
- Colored QR codes can occasionally cause decode failures with some
  scanners depending on the fill color's contrast against white; the
  OpenCV → PIL fallback in `decode_qr()` mitigates but doesn't eliminate
  this risk.
- The base64-detection logic is intentionally simple for this specific
  challenge and would benefit from a proper regex check if adapted for a
  challenge with a different number of encoded fragments or ordering.
