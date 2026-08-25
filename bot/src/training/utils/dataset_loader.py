from datasets import load_dataset
from pathlib import Path


def load_rick_dataset(dataset_path: str):
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {dataset_path}")

    dataset = load_dataset("json", data_files=str(path))
    return dataset
