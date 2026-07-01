# Hidden Flag in a 3D Model (.obj) — Write-up

## Challenge Overview

The challenge provides a `.obj` 3D model (a horned/demon-cat figurine, seen
below) with a CTF flag hidden inside it. Unlike the image-based challenges,
there's no encryption or pixel manipulation here — the `.obj` file format is
**plain text**, and the flag was simply planted as an extra named object
inside the file.

![3D model render](images/model_render.png)

*The model as rendered in a 3D viewer — nothing visually indicates a flag is
hidden; the trick lives in the file's text data, not its geometry.*

## Why This Works: the `.obj` Format

Wavefront `.obj` is a human-readable text format. A typical file looks like:

```
# Blender export
o Cat_Body
v 0.123 1.456 -0.789
v 0.234 1.567 -0.890
...
f 1 2 3
f 2 3 4

o Cat_Ears
v ...
f ...
```

Every mesh/sub-mesh in the file is introduced by an `o <name>` (object) line
— this name is just a free-text label the modeling software writes out, and
3D viewers generally ignore anything they don't recognize as geometry, so it
doesn't need to be a real mesh at all. Because of this, the challenge author
was able to insert an **extra `o` entry whose "name" is the flag itself**
(or a decoy object containing the flag string as its name/comment),
somewhere among the legitimate cat-mesh objects. A viewer just renders the
real geometry and silently skips or displays an empty/harmless entry for
the flag object — visually nothing looks out of place.

## Extraction

Since `.obj` is plain text, no special tooling is required — just read the
file as text and look for anything that doesn't belong. The simplest
approaches:

**Command line:**
```bash
grep -i "securinets" model.obj
# or scan all object/group names and comments:
grep -E "^(o|g|#)" model.obj
```

**Python:**
```python
with open("model.obj", "r", errors="ignore") as f:
    for line in f:
        if line.startswith(("o ", "g ", "#")):
            print(line.strip())
```

Either method surfaces the extra object whose name is the flag string,
rendered here as a screenshot of the matching line/comment:

![Extracted flag](images/flag_extracted.png)

## Flag

```
Securinets{Everybody_wanna_be_demon_til_they_get_chipped_by_a_throwaway}
```

## Notes / Caveats

- This class of stego relies on the fact that `.obj` (and many other 3D
  formats like `.stl` ASCII, `.ply` ASCII/ heade, `.gltf` JSON) keep
  human-readable metadata — object names, group names, comments, or even
  unused material/texture references — that most viewers don't validate or
  display. Any of these fields is a viable hiding spot.
- Binary 3D formats (`.glb`, binary `.stl`, `.fbx`) would require a
  different extraction approach — e.g. `strings model.glb | grep -i flag`
  or parsing embedded JSON/binary chunks — since plain `grep` on text lines
  wouldn't reliably find embedded strings in binary data.
- As a general checklist for "flag hidden in a 3D model" challenges: check
  object/group names, comments (`#`), material (`.mtl`) file references and
  names, texture file paths, and any custom/unknown vertex attributes before
  assuming the flag must be encoded in the geometry itself.
