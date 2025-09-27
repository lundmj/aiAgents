import sys
from pathlib import Path

def load_knowledge_files(knowledge_names: list[str]) -> list[dict]:
    """
    Read files from paths provided in knowledge_names and return system-role messages
    containing their text. Filenames are sanitized to basenames. Missing files are
    skipped with a warning.
    """
    messages: list[dict] = []
    base_dir = Path(__file__).parent

    def add_file(file_path: Path):
        safe = file_path.name
        try:
            text = file_path.read_text(encoding='utf-8')
            parts = [line.strip() for line in text.splitlines() if line.strip() != ""]
            content = " ".join(parts)
            messages.append({'role': 'system', 'content': f"[knowledge: {safe}] {content}"})
        except Exception as e:
            print(f"Warning: failed to read knowledge file {file_path}: {e}", file=sys.stderr)

    for name in knowledge_names:
        if not name:
            continue
        file_path = Path(name)
        if not file_path.exists():
            # also try relative to repository root / current working dir
            alt = base_dir / name
            if alt.exists():
                file_path = alt
            else:
                print(f"Warning: knowledge file not found: {name}", file=sys.stderr)
                continue
        if file_path.is_dir():
            for subfile in file_path.rglob('*'):
                if subfile.is_file():
                    add_file(subfile)
        elif file_path.is_file():
            add_file(file_path)
        else:
            print(f"Warning: {name} is neither a file nor a directory", file=sys.stderr)
    return messages