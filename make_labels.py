#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Frame, Paragraph


DEFAULT_CONFIG_PATH = Path("label_config.local.json")


def parse_one_off_address(address: str | None, lines: list[str] | None, delimiter: str) -> list[str]:
    if lines:
        return [line.strip() for line in lines if line and line.strip()]

    if not address:
        return []

    normalized = address.replace("\\n", "\n")
    if delimiter:
        normalized = normalized.replace(delimiter, "\n")

    return [line.strip() for line in normalized.splitlines() if line.strip()]


def row_to_lines(row: dict[str, str], address_column: str | None) -> list[str]:
    if address_column:
        value = (row.get(address_column) or "").strip()
        return [line.strip() for line in value.splitlines() if line.strip()]

    if "address" in row and (row.get("address") or "").strip():
        value = (row.get("address") or "").strip()
        return [line.strip() for line in value.splitlines() if line.strip()]

    lowered = {k.lower().strip(): (v or "").strip() for k, v in row.items()}

    direct_lines: list[str] = []
    for key in ("name", "company", "line1", "line2", "line3"):
        if lowered.get(key):
            direct_lines.append(lowered[key])

    city = lowered.get("city", "")
    state = lowered.get("state", "")
    postal = lowered.get("zip", "") or lowered.get("zipcode", "") or lowered.get("postal_code", "")

    city_state = " ".join(part for part in [city, state] if part).strip()
    if city_state and postal:
        direct_lines.append(f"{city_state} {postal}".strip())
    elif city_state:
        direct_lines.append(city_state)
    elif postal:
        direct_lines.append(postal)

    if lowered.get("country"):
        direct_lines.append(lowered["country"])

    if direct_lines:
        return direct_lines

    fallback_lines = [v.strip() for v in row.values() if v and v.strip()]
    return fallback_lines


def read_csv_addresses(csv_path: Path, address_column: str | None) -> list[list[str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise ValueError("CSV appears to have no header row.")

        if address_column and address_column not in reader.fieldnames:
            raise ValueError(
                f"Column '{address_column}' not found in CSV headers: {', '.join(reader.fieldnames)}"
            )

        labels: list[list[str]] = []
        for row in reader:
            lines = row_to_lines(row, address_column)
            if lines:
                labels.append(lines)
        return labels


def parse_return_lines(value: str | None, lines: list[str] | None, delimiter: str) -> list[str]:
    if lines:
        return [line.strip() for line in lines if line and line.strip()]

    if not value:
        return []

    normalized = value.replace("\\n", "\n")
    if delimiter:
        normalized = normalized.replace(delimiter, "\n")
    return [line.strip() for line in normalized.splitlines() if line.strip()]


def read_local_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            loaded = json.load(config_file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in config file '{config_path}': {error}") from error

    if not isinstance(loaded, dict):
        raise ValueError(f"Config file '{config_path}' must contain a JSON object.")

    return loaded


def get_return_lines(args: argparse.Namespace) -> list[str]:
    cli_lines = parse_return_lines(args.return_address, args.return_line, args.delimiter)
    if cli_lines:
        return cli_lines

    config_data = read_local_config(args.config)
    return_value = config_data.get("return_address")

    if isinstance(return_value, list):
        return [str(line).strip() for line in return_value if str(line).strip()]
    if isinstance(return_value, str):
        return parse_return_lines(return_value, None, args.delimiter)

    return []


def draw_label_page(
    pdf: canvas.Canvas,
    to_lines: Iterable[str],
    return_lines: list[str],
    font_size: int,
    margin_in: float,
    preview: bool,
    no_return: bool,
) -> None:
    width = 6 * inch
    height = 4 * inch
    margin = margin_in * inch

    return_style = ParagraphStyle(
        name="ReturnStyle",
        fontName="Helvetica",
        fontSize=max(10, int(font_size * 0.38)),
        leading=max(12, int(font_size * 0.48)),
    )

    recipient_font_size = max(10, int(font_size * 0.38))
    to_style = ParagraphStyle(
        name="ToStyle",
        fontName="Helvetica",
        fontSize=recipient_font_size,
        leading=max(12, int(recipient_font_size * 1.25)),
    )

    content_width = width - (2 * margin)
    content_height = height - (2 * margin)
    return_frame_x = margin
    return_frame_y = height - margin - 0.95 * inch
    return_frame_width = content_width * 0.58
    return_frame_height = 0.9 * inch

    to_frame_width = content_width * 0.50
    to_frame_height = 1.55 * inch
    to_frame_x = margin + (content_width * 0.34)
    to_frame_y = (height - to_frame_height) / 2

    if preview:
        pdf.saveState()
        pdf.setStrokeColorRGB(0.75, 0.75, 0.75)
        pdf.setLineWidth(0.8)
        pdf.rect(margin, margin, content_width, content_height, stroke=1, fill=0)
        pdf.setDash(3, 2)
        pdf.rect(return_frame_x, return_frame_y, return_frame_width, return_frame_height, stroke=1, fill=0)
        pdf.rect(to_frame_x, to_frame_y, to_frame_width, to_frame_height, stroke=1, fill=0)
        pdf.setDash()
        pdf.setFont("Helvetica", 8)
        pdf.drawString(return_frame_x + 2, return_frame_y + return_frame_height + 2, "RETURN")
        pdf.drawString(to_frame_x + 2, to_frame_y + to_frame_height + 2, "SHIP TO")
        pdf.restoreState()

    if return_lines and not no_return:
        return_html = "<br/>".join(escape(line) for line in return_lines)
        return_paragraph = Paragraph(return_html, style=return_style)
        return_frame = Frame(
            x1=return_frame_x,
            y1=return_frame_y,
            width=return_frame_width,
            height=return_frame_height,
            showBoundary=0,
        )
        return_frame.addFromList([return_paragraph], pdf)

    to_html = "<br/>".join(escape(line) for line in to_lines)
    to_paragraph = Paragraph(to_html, style=to_style)
    _, paragraph_height = to_paragraph.wrap(to_frame_width, to_frame_height)
    paragraph_height = min(paragraph_height, to_frame_height)
    to_text_y = to_frame_y + ((to_frame_height - paragraph_height) / 2)
    to_paragraph.drawOn(pdf, to_frame_x, to_text_y)
    pdf.showPage()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate 6x4 shipping label PDFs from a CSV file or one-off address input."
    )
    parser.add_argument("--csv", type=Path, help="Path to CSV file containing address rows.")
    parser.add_argument(
        "--address",
        help="One-off address text. Use '|', \\n, or --line multiple times for line breaks.",
    )

    parser.add_argument(
        "--line",
        action="append",
        help="One-off address line (repeat for multiple lines). Overrides --address when used.",
    )
    parser.add_argument(
        "--address-column",
        help="CSV column that contains full multi-line address text (e.g., 'address').",
    )
    parser.add_argument(
        "--delimiter",
        default="|",
        help="Delimiter for splitting --address into lines (default: '|').",
    )
    parser.add_argument(
        "--return-address",
        help="Return address text for top-left block. Use '|', \\n, or --return-line.",
    )
    parser.add_argument(
        "--return-line",
        action="append",
        help="Single return address line (repeat for multiple lines). Overrides --return-address.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Local JSON config path (default: label_config.local.json).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("labels.pdf"),
        help="Output PDF path (default: labels.pdf).",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=28,
        help="Label font size in points (default: 28).",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.25,
        help="Page margin in inches (default: 0.25).",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Draw light guide boxes/labels to help align layout before final print.",
    )
    parser.add_argument(
        "--no-return",
        action="store_true",
        help="Do not render return-address content on labels.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.font_size <= 0:
        parser.error("--font-size must be greater than 0")
    if args.margin < 0 or args.margin >= 2:
        parser.error("--margin must be in the range [0, 2)")

    labels: list[list[str]] = []

    has_csv = bool(args.csv)
    has_one_off = bool(args.address or args.line)

    if has_csv and has_one_off:
        parser.error("Use either CSV mode (--csv) or one-off mode (--address/--line), not both.")
    if not has_csv and not has_one_off:
        parser.error("Provide --csv for batch mode, or --address/--line for one-off mode.")

    if has_csv:
        if not args.csv.exists():
            parser.error(f"CSV file not found: {args.csv}")
        try:
            labels = read_csv_addresses(args.csv, args.address_column)
        except ValueError as error:
            parser.error(str(error))
    else:
        one_off_lines = parse_one_off_address(args.address, args.line, args.delimiter)
        if not one_off_lines:
            parser.error("No address content found. Provide --address or one or more --line values.")
        labels = [one_off_lines]

    if not labels:
        parser.error("No non-empty labels found to render.")

    try:
        return_lines = get_return_lines(args)
    except ValueError as error:
        parser.error(str(error))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(args.output), pagesize=(6 * inch, 4 * inch))
    pdf.setViewerPreference("PrintScaling", "None")

    for label in labels:
        draw_label_page(
            pdf,
            label,
            return_lines,
            args.font_size,
            args.margin,
            args.preview,
            args.no_return,
        )

    pdf.save()
    print(f"Created {len(labels)} label(s): {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
