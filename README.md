# Thermal Label Maker

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Labels](https://img.shields.io/badge/label-size%206x4-informational.svg)](docs/README.md)

Printer-ready 6x4 shipping-label PDF generator for thermal workflows.

Generate one label per page from:
- one-off CLI address input, or
- CSV batch address data.

Includes return-address support, preview guides, and local-only config for sender details.

## Features

- Exact 6x4 PDF pages (`432 x 288` points)
- One label per page (batch-safe)
- One-off mode (`--line` or `--address`)
- CSV mode (`--csv` + optional `--address-column`)
- Return address via CLI or local config file
- Preview guides (`--preview`) and optional return hiding (`--no-return`)

## Requirements

- Python 3.10+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

One-off label:

```bash
.venv/bin/python make_labels.py \
  --line "Jane Doe" \
  --line "123 Example St" \
  --line "Springfield, IL 62701" \
  --return-line "Your Company Name" \
  --return-line "456 Sender Ave" \
  --return-line "Austin, TX 78701" \
  --output docs/labels.pdf
```

Batch from CSV:

```bash
.venv/bin/python make_labels.py --csv sample_addresses.csv --output docs/labels.pdf
```

## Return Address Options

Use CLI flags:

```bash
--return-line "Line 1" --return-line "Line 2" --return-line "Line 3"
```

Or use local config:

1. Copy template:

```bash
cp label_config.example.json label_config.local.json
```

2. Edit `label_config.local.json` with your return address.

This file is ignored by git and stays local.

## Print Notes (Thermal)

The PDF is authored at 6x4. In the print dialog:
- Paper size: `4x6` (or `6x4`, depending on orientation)
- Scale: `100%` / `Actual Size`
- Disable `Fit to page`

## Included Files

- `make_labels.py`: CLI generator
- `sample_addresses.csv`: sample batch input (column-per-field format)
- `sample_addresses_up.csv`: second sample batch input
- `.claude/skills/thermal-label-maker/SKILL.md`: Claude skill workflow

## Documentation

Additional usage notes: [docs/README.md](docs/README.md)

## License

MIT — see [LICENSE](LICENSE)
