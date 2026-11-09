---
name: thermal-label-maker
description: Generate 6x4 one-label-per-page shipping label PDFs from a return address and a list of destination addresses using make_labels.py.
---

# Thermal Label Maker Skill

Use this skill when the user asks for shipping labels and provides:
- A return address
- One or more destination addresses

This skill uses the repository CLI:
- `make_labels.py`

## Inputs to collect

Required:
- Return address (2-4 lines)
- Destination addresses (one or more; each address should be multi-line)

Optional:
- Output filename (default: `docs/labels.pdf`)
- Preview mode (`--preview`)
- Hide return text (`--no-return`)

If the user gives freeform text, normalize it into:
- `return_lines: list[str]`
- `address_blocks: list[list[str]]`

## Execution workflow

1. Create a temporary CSV with one column named `address` where each row is a newline-joined destination address.
2. Run `make_labels.py` in CSV mode with `--address-column address`.
3. Pass the return address using repeated `--return-line` flags.
4. Save output under `docs/` unless the user requested another path.

## Command recipe

From repository root:

```bash
python3 - <<'PY'
import csv
from pathlib import Path

rows = [
    # Replace with destination address blocks, one list per label
    ["Jane Doe", "123 Example St", "Springfield IL 62701"],
    ["John Smith", "789 Sample Rd Apt 4", "Portland OR 97201"],
]

out = Path("docs/.tmp_skill_addresses.csv")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["address"])
    writer.writeheader()
    for block in rows:
        writer.writerow({"address": "\n".join(line.strip() for line in block if line.strip())})
print(out)
PY

python3 make_labels.py \
  --csv docs/.tmp_skill_addresses.csv \
  --address-column address \
  --return-line "Your Company Name" \
  --return-line "456 Sender Ave" \
  --return-line "Austin TX 78701" \
  --output docs/labels.pdf
```

Optional flags to append:
- `--preview`
- `--no-return`

## Behavior rules

- Keep one label per page (default behavior of this project).
- Do not modify `label_config.local.json` unless the user explicitly asks.
- Prefer writing generated PDFs to `docs/`.
- If any destination block is missing critical lines, ask a focused follow-up before generating.
- After generation, report the output PDF path and number of labels created.

## Example user intent mapping

User:
- "Here is my return address ... and here are 12 addresses I need labels for"

Assistant using this skill should:
1. Parse return block and 12 destination blocks.
2. Build temporary CSV as above.
3. Run `make_labels.py` with repeated `--return-line` flags.
4. Return: `Created 12 label(s): docs/<filename>.pdf`.
