# Thermal Label Maker Docs

Generate one 6x4 label per PDF page using `make_labels.py`.

## Quick use

```bash
.venv/bin/python make_labels.py --line "Name" --line "Street" --line "City ST ZIP" --output docs/labels.pdf
```

Or from CSV:

```bash
.venv/bin/python make_labels.py --csv sample_addresses.csv --output docs/labels.pdf
```

## Printing exactly 6x4

Generated PDFs are sized to 6x4 inches and include a no-scaling print preference.

In your print dialog, make sure:

- Paper size is `4 in x 6 in` (or `6 in x 4 in`, depending on orientation)
- Scale is `100%` / `Actual Size`
- `Fit to page` is OFF
- Auto-rotate/center can be ON if your printer expects portrait media
