from pathlib import Path


def get_project_version() -> str:
    version_file = Path(__file__).resolve().parents[3] / "VERSION"
    try:
        version = version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "V0.0.0"
    return version or "V0.0.0"
