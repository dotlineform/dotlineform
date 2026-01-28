#!/usr/bin/env python3
"""
Generate Jekyll work pages from an Excel workbook.

This repo stores works as a Jekyll collection in `_works/`. The generator writes one Markdown
file per work (e.g. `_works/00286.md`) with YAML front matter populated from three worksheets:

- Works: base work metadata (1 row per work)
- WorkImages: images joined by work_id (0..n rows per work)
- WorkAttachments: attachments joined by work_id (0..n rows per work)

YAML typing rules enforced by this script (so Excel cells do NOT need quoting):
- Numbers are emitted unquoted for: year, height_cm, width_cm, depth_cm
- Everything else is emitted as a quoted string (including dates like catalogue_date and fields like year_display)
- Empty cells become YAML null

Safe by default:
- dry-run unless you pass --write
- will not overwrite unless --force

Example:
  python3 scripts/generate_work_pages.py data/works.xlsx --write
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import hashlib
import json

import openpyxl


# ----------------------------
# Helpers (ID/date/YAML parsing)
# ----------------------------
# These functions exist to normalise common Excel quirks (e.g. numeric IDs like 361.0)
# and to keep YAML output safe/consistent.
def slug_id(raw: Any, width: int = 5) -> str:
    if raw is None:
        raise ValueError("Missing id")
    s = str(raw).strip()
    # Handle numeric IDs like 361.0 from Excel
    s = re.sub(r"\.0$", "", s)
    # NOTE: This strips ALL non-digits. If your IDs ever include prefixes/suffixes, change this logic.
    s = re.sub(r"\D", "", s)  # keep digits only
    if not s:
        raise ValueError(f"Invalid id value: {raw!r}")
    return s.zfill(width)


def parse_date(raw: Any) -> Optional[str]:
    if raw is None or str(raw).strip() == "":
        return None
    if isinstance(raw, dt.datetime):
        return raw.date().isoformat()
    if isinstance(raw, dt.date):
        return raw.isoformat()
    s = str(raw).strip()
    # NOTE: Prefer real Excel date cells or ISO strings in the workbook; anything else may pass through unchanged.
    # Accept YYYY-M-D and normalise to YYYY-MM-DD if possible
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, mo, d = map(int, m.groups())
        return dt.date(y, mo, d).isoformat()
    # Last resort: leave as-is (but you should fix upstream)
    return s


def parse_list(raw: Any, sep: str = ",") -> List[str]:
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    return [item.strip() for item in s.split(sep) if item.strip()]


def yaml_quote(s: str) -> str:
    """Quote a string safely for YAML."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


NUMERIC_KEYS = {"year", "height_cm", "width_cm", "depth_cm"}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def coerce_numeric(value: Any) -> Optional[float]:
    """Best-effort numeric coercion for dimension fields; returns None if not parseable."""
    if is_empty(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except Exception:
        return None


def coerce_int(value: Any) -> Optional[int]:
    """Best-effort integer coercion for year; returns None if not parseable."""
    if is_empty(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    try:
        return int(str(value).strip())
    except Exception:
        return None


def coerce_string(value: Any) -> Optional[str]:
    """Coerce any non-empty value to a trimmed string (for quoted YAML output)."""
    if is_empty(value):
        return None
    return str(value).strip()


def dump_scalar(key: str, value: Any) -> str:
    """Dump a scalar YAML key/value with typing rules."""
    if value is None:
        return f"{key}: null"

    if key in NUMERIC_KEYS:
        # year is an int; dimensions are floats but we render ints without .0
        if key == "year":
            iv = coerce_int(value)
            return f"{key}: {iv}" if iv is not None else f"{key}: null"
        fv = coerce_numeric(value)
        if fv is None:
            return f"{key}: null"
        if fv.is_integer():
            return f"{key}: {int(fv)}"
        return f"{key}: {fv}"

    # Everything else is a quoted string
    sv = coerce_string(value)
    return f"{key}: {yaml_quote(sv)}" if sv is not None else f"{key}: null"


def dump_list_of_strings(key: str, values: List[str]) -> List[str]:
    lines: List[str] = [f"{key}:"]
    for v in values:
        lines.append(f"  - {yaml_quote(str(v))}")
    return lines


def dump_list_of_dicts(key: str, items: List[Dict[str, Any]], field_order: Optional[List[str]] = None) -> List[str]:
    """Dump a YAML list of dicts with stable key ordering."""
    lines: List[str] = [f"{key}:"]
    for item in items:
        # First line for each item
        lines.append("  -")
        keys = field_order if field_order else list(item.keys())
        for k in keys:
            if k not in item:
                continue
            # All nested fields here are strings by design; emit as quoted string or null
            sv = coerce_string(item.get(k))
            if sv is None:
                lines.append(f"    {k}: null")
            else:
                lines.append(f"    {k}: {yaml_quote(sv)}")
    return lines



def build_front_matter(fields: Dict[str, Any]) -> str:
    """Build YAML front matter in block style (supports lists of dicts)."""
    # Policy: we intentionally emit explicit empty values to keep the front matter schema stable.
    # - Empty/blank scalars become `key: null`
    # - Empty lists become `key: []`
    # This makes diffs, validation, and layout logic simpler and easier to test.
    lines: List[str] = ["---"]

    for k, v in fields.items():
        if isinstance(v, list):
            if not v:
                # Emit empty list explicitly (rare; keeps schema predictable)
                lines.append(f"{k}: []")
                continue

            # Detect list of dicts vs list of strings
            if all(isinstance(x, dict) for x in v):
                if k == "images":
                    lines.extend(dump_list_of_dicts(k, v, field_order=["file", "caption", "alt"]))
                elif k == "attachments":
                    lines.extend(dump_list_of_dicts(k, v, field_order=["file", "label"]))
                else:
                    lines.extend(dump_list_of_dicts(k, v))
            else:
                # List of scalars -> strings
                lines.extend(dump_list_of_strings(k, [str(x) for x in v if not is_empty(x)]))
            continue

        # Scalars
        lines.append(dump_scalar(k, v))

    lines.append("---")
    return "\n".join(lines) + "\n"


# ----------------------------
# Canonical schema (Works sheet)
# ----------------------------
# Define the Works->front matter mapping once so adding a new field is a one-line change.
# Each entry is: (front_matter_key, excel_column_name, coercer)
# Coercers should return the Python type we want before YAML emission:
# - strings (quoted), ints/floats (unquoted for configured numeric keys), or None (-> null)
WORKS_SCHEMA: List[tuple[str, str, Any]] = [
    ("artist", "artist", coerce_string),
    ("title", "title", coerce_string),
    ("year", "year", coerce_int),
    ("year_display", "year_display", coerce_string),
    ("series", "series", coerce_string),
    ("medium_type", "medium_type", coerce_string),
    ("medium_caption", "medium_caption", coerce_string),
    ("duration", "duration", coerce_string),
    ("height_cm", "height_cm", coerce_numeric),
    ("width_cm", "width_cm", coerce_numeric),
    ("depth_cm", "depth_cm", coerce_numeric),
    # tags handled separately (csv list)
    ("catalogue_date", "catalogue_date", parse_date),
    ("orientation", "orientation", coerce_string),
    ("storage_location", "storage_location", coerce_string),
    ("provenance", "provenance", coerce_string),
    # checksum is always computed, not sourced from Excel
    ("notes_private", "notes_private", coerce_string),
]


def build_works_front_matter(works_row: tuple, works_hi: Dict[str, int]) -> Dict[str, Any]:
    """Build the scalar portion of Works front matter (excluding work_id, tags, images, attachments)."""
    fm: Dict[str, Any] = {}
    for fm_key, col_name, coercer in WORKS_SCHEMA:
        raw = works_row[works_hi[col_name]] if col_name in works_hi else None
        fm[fm_key] = coercer(raw)
    return fm


# ----------------------------
# Checksum helpers
# ----------------------------

def _sort_key_safe(v: Optional[str]) -> str:
    return "" if v is None else str(v)


def compute_work_checksum(front_matter: Dict[str, Any]) -> str:
    """Compute a deterministic checksum for a work from its front matter (excluding checksum itself)."""
    payload = dict(front_matter)
    payload.pop("checksum", None)

    images = payload.get("images")
    if isinstance(images, list):
        images_sorted = sorted(
            images,
            key=lambda d: (
                _sort_key_safe(d.get("file")),
                _sort_key_safe(d.get("caption")),
                _sort_key_safe(d.get("alt")),
            ),
        )
        payload["images"] = images_sorted

    attachments = payload.get("attachments")
    if isinstance(attachments, list):
        attachments_sorted = sorted(
            attachments,
            key=lambda d: (_sort_key_safe(d.get("file")), _sort_key_safe(d.get("label"))),
        )
        payload["attachments"] = attachments_sorted

    # Canonical JSON for hashing (sorted keys ensures deterministic output)
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    h = hashlib.blake2b(canonical, digest_size=16)
    return h.hexdigest()


def extract_existing_checksum(path: Path) -> Optional[str]:
    """Extract `checksum` from the YAML front matter of an existing work page."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    # Only inspect the first YAML front matter block
    if not text.startswith("---"):
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    fm_text = parts[1]
    for line in fm_text.splitlines():
        if not line.startswith("checksum:"):
            continue
        _, raw = line.split(":", 1)
        raw = raw.strip()
        if raw == "null" or raw == "":
            return None
        if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
            return raw[1:-1]
        return raw

    return None


# ----------------------------
# Main program
# ----------------------------
# High-level flow:
# 1) Parse CLI args (column mapping + output options)
# 2) Load workbook + sheets
# 3) Build header->index maps from row 1 of each sheet
# 4) Iterate Works rows -> build front matter + body -> write one file per work
def main() -> None:
    # CLI arguments define how we map Excel columns to front matter fields, and where output files go.
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx", help="Path to Excel workbook (.xlsx)")

    # Worksheet names
    ap.add_argument("--works-sheet", default="Works", help="Worksheet name for base work metadata")
    ap.add_argument("--images-sheet", default="WorkImages", help="Worksheet name for work images")
    ap.add_argument("--attachments-sheet", default="WorkAttachments", help="Worksheet name for work attachments")

    # Output
    ap.add_argument("--output-dir", default="_works", help="Output folder for generated work pages")

    # Write controls
    ap.add_argument("--write", action="store_true", help="Actually write files (otherwise dry-run)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = ap.parse_args()

    # Resolve the workbook path and fail fast if it is missing.
    xlsx_path = Path(args.xlsx).expanduser()
    if not xlsx_path.exists():
        raise SystemExit(f"Workbook not found: {xlsx_path}")

    # `data_only=True` reads the last-calculated values of formula cells.
    # If your sheet relies on formulas that haven't been calculated/saved, values may be None.
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)

    def read_sheet_rows(sheet_name: str) -> List[tuple]:
        if sheet_name not in wb.sheetnames:
            raise SystemExit(f"Sheet not found in workbook: {sheet_name}")
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        return rows

    def build_header_index(rows: List[tuple]) -> Dict[str, int]:
        if not rows:
            return {}
        headers = [str(h).strip() if h is not None else "" for h in rows[0]]
        return {h: i for i, h in enumerate(headers) if h}

    def cell(row: tuple, header_index: Dict[str, int], col_name: str) -> Any:
        i = header_index.get(col_name)
        return None if i is None or i >= len(row) else row[i]

    # Output directory:
    # - Use `works` for a normal pages folder.
    # - Use `_works` if you're using a Jekyll collection.
    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load all worksheets up-front.
    works_rows = read_sheet_rows(args.works_sheet)
    images_rows = read_sheet_rows(args.images_sheet)
    attachments_rows = read_sheet_rows(args.attachments_sheet)

    if not works_rows:
        raise SystemExit(f"Works sheet '{args.works_sheet}' is empty")

    works_hi = build_header_index(works_rows)
    images_hi = build_header_index(images_rows) if images_rows else {}
    attachments_hi = build_header_index(attachments_rows) if attachments_rows else {}

    # Pre-index images by work_id
    images_by_work: Dict[str, List[Dict[str, Any]]] = {}
    for r in images_rows[1:] if len(images_rows) > 1 else []:
        raw_wid = cell(r, images_hi, "work_id")
        if is_empty(raw_wid):
            continue
        wid = slug_id(raw_wid)
        img = {
            "file": coerce_string(cell(r, images_hi, "file")),
            "caption": coerce_string(cell(r, images_hi, "caption")),
            "alt": coerce_string(cell(r, images_hi, "alt")),
        }
        # Drop entries with no file
        if is_empty(img.get("file")):
            continue
        images_by_work.setdefault(wid, []).append(img)

    # Pre-index attachments by work_id
    attachments_by_work: Dict[str, List[Dict[str, Any]]] = {}
    for r in attachments_rows[1:] if len(attachments_rows) > 1 else []:
        raw_wid = cell(r, attachments_hi, "work_id")
        if is_empty(raw_wid):
            continue
        wid = slug_id(raw_wid)
        att = {
            "file": coerce_string(cell(r, attachments_hi, "file")),
            "label": coerce_string(cell(r, attachments_hi, "label")),
        }
        if is_empty(att.get("file")):
            continue
        attachments_by_work.setdefault(wid, []).append(att)

    written = 0
    skipped = 0
    total = max(len(works_rows) - 1, 0)  # exclude header row
    processed = 0

    # Iterate each Works row and emit one Markdown file per work.
    for r in works_rows[1:]:
        processed += 1
        prefix = f"[{processed}/{total}] "
        raw_work_id = cell(r, works_hi, "work_id")
        if is_empty(raw_work_id):
            skipped += 1
            continue

        wid = slug_id(raw_work_id)

        # Tags: comma-separated in Excel
        tags = parse_list(cell(r, works_hi, "tags"), sep=",")

        # Fields in stable order (matches your canonical front matter schema)
        fm: Dict[str, Any] = {"work_id": wid}
        fm.update(build_works_front_matter(r, works_hi))
        fm["tags"] = tags

        # Join in images/attachments from their respective sheets
        imgs = images_by_work.get(wid, [])
        atts = attachments_by_work.get(wid, [])
        if imgs:
            fm["images"] = imgs
        if atts:
            fm["attachments"] = atts

        # Compute checksum from the canonical Excel-derived record and write it into front matter.
        checksum = compute_work_checksum(fm)
        fm["checksum"] = checksum

        content = build_front_matter(fm) + "\n"

        out_path = out_dir / f"{wid}.md"
        exists = out_path.exists()

        existing_checksum = extract_existing_checksum(out_path) if exists else None
        if (existing_checksum is not None) and (existing_checksum == checksum) and (not args.force):
            print(f"{prefix}SKIP (checksum match): {out_path}")
            skipped += 1
            continue

        if args.write:
            out_path.write_text(content, encoding="utf-8")
            print(f"{prefix}WRITE: {out_path}")
            written += 1
        else:
            print(f"{prefix}DRY-RUN: would write {out_path} (overwrite={exists})")
            written += 1

    print(f"\nDone. {'Would write' if not args.write else 'Wrote'}: {written}. Skipped: {skipped}.")


if __name__ == "__main__":
    main()