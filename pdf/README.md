# Tic-Tac-Toe in a PDF — Hidden Flag Write-up

## Challenge Overview

The challenge is a single PDF containing a fully playable, interactive
Tic-Tac-Toe game built entirely out of PDF **AcroForm** fields and embedded
**JavaScript** (a document-level `/JavaScript` action named `GameLogic`).
Rendered, it looks completely benign:

![Rendered PDF](images/pdf_render.png)

*A 3×3 grid of clickable text fields, a "Current Player" status bar, and a
red Reset button — nothing here visually hints at a flag.*

The flag isn't hidden in the PDF's visible content or metadata — it's
constructed **at runtime by the obfuscated JavaScript**, inside the
`checkWinner()` function, and would only ever be *displayed* to a player who
actually won a game (via `app.alert(...)`). It doesn't need to be played to
be extracted, though — the string is built from **fixed, non-random pieces**,
so it can be recovered purely by reading the script statically.

## How the PDF Is Structured

- `/AcroForm` defines 11 form fields (`/Fields [3 0 R ... 13 0 R]`):
  9 text-field "cells" (`cell0`–`cell8`), a read-only `status` field, and a
  `reset` push-button.
- Each cell's `/AA` (additional-actions) dictionary fires a `/U` (mouse-up)
  JavaScript action — `makeMove(0);`, `makeMove(1);`, etc. — wiring clicks
  to game logic.
- The actual game logic lives in a single named JavaScript entry under
  `/Names /JavaScript`, called `GameLogic`, which defines `makeMove()`,
  `checkWinner()`, `resetGame()`, and a couple of obfuscation helper
  functions (`_0x1f59`, `_0x2d8d`).
- Page content (`14 0 R` → contents `16 0 R`) just draws the title text and
  the grid/box outlines seen in the render — pure static PDF drawing
  operators (`re`, `S`, `Tj`), nothing hidden there.

## Deobfuscating the JavaScript

The script is run through a typical **string-array + offset-lookup**
obfuscator (the pattern JS obfuscators like `javascript-obfuscator` produce):

```javascript
function _0x2d8d(){
  var _0x3e0831 = ['es{','Player ','\x20wins!','Current\x20Player:\x20',
    '_fi_TASK}','ATLi_','textColor','value','262550fJUufN','43184oMHktX',
    'status','getField','alert','502896rMKvVF','4132640DgKLtm',
    '547593liXoXL','139597KKisTu','T_EssM','2agKdcd','1006132RSekOO',
    'readonly','387sxpzWk','21kNZcin','Game\x20Over','toString','cell'];
  _0x2d8d = function(){ return _0x3e0831; };
  return _0x2d8d();
}
```

All real strings the script uses (`'status'`, `'getField'`, `'cell'`,
message fragments, etc.) — plus a handful of decoy numeric-looking junk
strings (`'262550fJUufN'`, `'43184oMHktX'`, etc., never actually
referenced) — are stashed in this one array. A second helper does the
lookup with a constant offset:

```javascript
function _0x1f59(id) {
  var arr = _0x2d8d();
  return arr[id - 0x137];   // 0x137 = 311
}
```

So anywhere the code calls e.g. `_0x1f59(0x14f)`, that's really just
`arr[0x14f - 0x137]` → `arr[24]` → the string `"es{"`. This is purely
**index-offset obfuscation** (no runtime array shuffling here — the
self-invoking IIFE above it is a decoy/anti-tamper check pattern common to
this obfuscator family, but it doesn't reorder `_0x3e0831`), so once you
know the offset, every call resolves to a fixed string.

## Reconstructing the Flag

The flag is built inside `checkWinner()`:

```javascript
var flagStr =
    String.fromCharCode(0x53)        // 'S'
  + 'ecurint'
  + _0x1f59(0x14f)                   // 'es{'
  + 'M' + (0x2 + 0x1)                // 'M3'
  + 'r' + (0xa + 0x3)                // 'r13'
  + 'M_'
  + (9).toString(0x24).toUpperCase() // base-36 of 9 -> '9'
  + _0x1f59(0x13a)                   // 'ATLi_'
  + 0x7 * 0xa                        // 70
  + _0x1f59(0x146)                   // 'T_EssM'
  + (0x0 + 0x1)                      // '1'
  + _0x1f59(0x139);                  // '_fi_TASK}'
```

Every piece here is a **compile-time constant** — character codes, small
hex arithmetic, and fixed array lookups. Nothing depends on game state,
randomness, or user input, so the safest way to recover it is to **not**
open the PDF in a JS-enabled viewer (Acrobat) at all, and instead extract
and evaluate just this expression in an isolated sandbox:

```bash
node decode_flag.js
```

```javascript
// decode_flag.js — only the string-table + lookup helper + the
// flag-building expression, copied verbatim from the PDF's /JS entry.
// No PDF object model, no `app`, no `this.getField` calls included —
// those aren't needed to compute the flag string.
```

Running it prints:

```
Securintes{M3r13M_9ATLi_70T_EssM1_fi_TASK}
```

## Flag

```
Securintes{M3r13M_9ATLi_70T_EssM1_fi_TASK}
```

## Notes / Caveats

- **Never execute untrusted PDF JavaScript in a full-featured reader**
  (Acrobat, Foxit, etc.) to "just see what it does" — PDF JS has access to
  `app.*`, form/doc-level APIs, and historically has been a real-world
  malware delivery vector. The correct approach for a challenge like this
  is exactly what's shown above: extract the `/JS` string statically
  (`grep`, `qpdf --qdf`, `pikepdf`, `pdf-parser.py`, etc.) and evaluate only
  the pieces you need in a throwaway sandbox (plain Node with no filesystem
  work, a browser dev-console with network disabled, etc.) — never inside
  the real PDF viewer context.
- The obfuscation here is entirely cosmetic from a *value* standpoint — no
  branch depends on hidden randomness or external state, so nothing about
  actually playing the game is required to recover the flag. Playing the
  game to a win would just trigger `app.alert()` with this same string —
  a valid but unnecessarily slow path to the same answer.
- The array in `_0x2d8d()` contains several strings that look like
  obfuscator "junk"/anti-optimization counters (e.g. `'262550fJUufN'`) —
  these are never referenced by any `_0x1f59(...)` call in the surrounding
  code and can be ignored; they're artifacts of the obfuscator's control-flow
  flattening, not meaningful data.
