import json
import pandas

from pathlib import Path
from text_cleaning_utils import clean_line


def load_csv(path: Path) -> list[str]:
    df = pandas.read_csv(path)
    lines = []

    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        line = str(row.get("line", "")).strip()

        if name != "Rick":
            continue

        cleaned = clean_line(line)
        if not cleaned:
            continue

        lines.append(cleaned)

    return lines


def load_quotes(path: Path) -> list[str]:
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f.readlines():
            raw = raw.strip().strip('"')
            cleaned = clean_line(raw)
            if cleaned:
                lines.append(cleaned)
    return lines


def save_jsonl(lines: list[str], out_path: Path):
    with open(out_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps({"text": line}, ensure_ascii=False) + "\n")


def dedupe_lines(lines: list[str]) -> list[str]:
    """Deduplicate lines using a normalized key."""
    seen = set()
    unique = []

    for line in lines:
        key = line.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(line)

    return unique


def main():
    root = Path(__file__).resolve().parents[2]
    csv_path = root / "data" / "raw" / "rick_and_morty_transcripts.csv"
    quotes_path = root / "data" / "raw" / "rick_quotes.txt"
    out_path = root / "data" / "processed" / "rick_lines.jsonl"

    csv_lines = load_csv(csv_path)
    quote_lines = load_quotes(quotes_path)
    all_lines = dedupe_lines(csv_lines + quote_lines)

    save_jsonl(all_lines, out_path)
    print(f"Saved {len(all_lines)} cleaned Rick lines to {out_path}")


if __name__ == "__main__":
    main()
