import json

from bot.src.training.utils.logging_utils import setup_logging
from pathlib import Path


def load_jsonl(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = obj.get("text", "").strip()
                if text:
                    items.append({"text": text})
            except json.JSONDecodeError:
                continue
    return items


def main():
    logger = setup_logging()

    # Input files
    rick_lines_path = Path("bot/data/processed/rick_lines.jsonl")
    synthetic_path = Path("bot/data/processed/synthetic_monologues.jsonl")

    # Output file
    merged_output_path = Path("bot/data/processed/rick_dataset.jsonl")

    logger.info("Loading Rick lines...")
    rick_lines = load_jsonl(rick_lines_path)
    logger.info(f"Loaded {len(rick_lines)} Rick lines")

    logger.info("Loading synthetic monologues...")
    synthetic_lines = load_jsonl(synthetic_path)
    logger.info(f"Loaded {len(synthetic_lines)} synthetic monologues")

    # Merge
    merged = synthetic_lines + rick_lines
    logger.info(f"Merged total: {len(merged)} entries")

    # Save merged dataset
    with merged_output_path.open("w", encoding="utf-8") as f:
        for item in merged:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info(f"Saved merged dataset to {merged_output_path}")


if __name__ == "__main__":
    main()
