"""Reorder data/collect7.txt by timestamp and reassign sequential IDs.

This script ensures that the file is chronological and that the "id" column is
consecutive from 1.

It preserves the header lines ("# ..." and "[weatherbit]") and the column
line, then writes back a sorted version of the data.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def parse_row(line: str) -> tuple[int, datetime, str]:
    parts = line.strip().split(",")
    if len(parts) < 2:
        raise ValueError("Malformed row")
    row_id = int(parts[0])
    ts = datetime.fromisoformat(parts[1])
    return row_id, ts, line


def main() -> None:
    path = Path("data/collect7.txt")
    if not path.exists():
        raise SystemExit("data/collect7.txt does not exist")

    lines = path.read_text(encoding="utf-8").splitlines()

    header = []
    data_lines = []

    for line in lines:
        if not line.strip():
            continue
        if line.startswith("#") or line.startswith("[") or line.startswith("id,"):
            header.append(line)
        else:
            data_lines.append(line)

    parsed = []
    for line in data_lines:
        try:
            _, ts, _ = parse_row(line)
        except Exception:
            continue
        parsed.append((ts, line))

    parsed.sort(key=lambda x: x[0])

    output_lines = []
    output_lines.extend(header)

    # rewrite data rows with sequential IDs
    for idx, (_, line) in enumerate(parsed, start=1):
        parts = line.split(",")
        parts[0] = str(idx)
        output_lines.append(",".join(parts))

    path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(f"Reordered {len(parsed)} rows and rewrote {path}")


if __name__ == "__main__":
    main()
