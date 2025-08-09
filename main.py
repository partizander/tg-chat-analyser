import json
import sys
import os
from pathlib import Path
from yaml import safe_load
from processors import REGISTRY

class ChatAnalyser:
    def __init__(self, filepath: Path):
        self.filepath = filepath

    def load_data(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("messages", [])

def load_config(path: Path) -> list[str]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = safe_load(f) or {}
    return data.get("processors", [])

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_json> <output_dir> [config.yaml]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    config_path = Path(sys.argv[3]) if len(sys.argv) >= 4 else Path("config.yaml")

    if not filepath.exists():
        cwd = os.getcwd()
        print(f"File {cwd}/{filepath} not found")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"read from {filepath}")
    messages = ChatAnalyser(filepath).load_data()
    processor_names = load_config(config_path)

    for name in processor_names:
        cls = REGISTRY.get(name)
        if not cls:
            print(f"unknown processor: {name}")
            continue
        try:
            processor = cls(output_dir=output_dir)
        except TypeError:
            processor = cls()
        processor.run(messages)

if __name__ == "__main__":
    main()
