# Release Notes — v1.1.0

**Released:** 2026-04-29

---

## What's new

### Lossless PNG output

Variations are now exported as PNG files instead of JPEG. This eliminates compression artefacts and makes output assets suitable for direct use in print, motion, or brand work — no extra export step needed.

### Hex colour names in filenames

Each file is now named after the two colours it contains, in standard hex notation:

```text
083_2CD2B4_DC1E5A.png
```

You can copy the hex value directly from the filename into Figma, Illustrator, Photoshop, or your design system — no more decoding raw integer tuples.

### `colors.csv` sidecar

Every batch now produces a `colors.csv` file in the output folder:

| variation | color_1_hex | color_2_hex |
| --------- | ----------- | ----------- |
| 0         | #2CD2B4     | #DC1E5A     |
| 1         | #A3F060     | #3B1CFF     |
| …         | …           | …           |

This makes it easy to share, document, or import the full palette into a spreadsheet or design token workflow.

---

## Bug fix

A channel-order error meant that the red and blue values in saved images were swapped relative to the colours used in the blend calculation. As a result, a variation labelled with a warm red/orange pair could render as a cool blue/cyan pair on screen. This is now corrected — the hex names in filenames accurately reflect the colours visible in the image.

---

## Upgrade notes

No changes to how the tool is invoked. Run `python3 duotone_generator.py` as before. The only difference you will notice is the output folder: PNG files with hex names and a new `colors.csv` alongside them.

No new dependencies are required. `csv` is part of the Python standard library.
