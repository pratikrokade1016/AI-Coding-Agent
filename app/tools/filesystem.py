from pathlib import Path

IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "venv",
    ".venv",
    "node_modules",
}


def list_files(directory: str | Path) -> list[str]:
    """Return source files recursively while ignoring generated directories."""
    root = Path(directory).resolve()

    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")

    if not root.is_dir():
        raise ValueError(f"Path is not a directory: {root}")

    files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue

        files.append(str(path))

    return sorted(files)


def _safe_path(root: str | Path, requested: str | Path) -> Path:
    """Ensure the requested path stays inside the allowed workspace."""
    root_path = Path(root).resolve()
    requested_path = Path(requested)

    if not requested_path.is_absolute():
        requested_path = root_path / requested_path

    requested_path = requested_path.resolve()

    try:
        requested_path.relative_to(root_path)
    except ValueError as exc:
        raise PermissionError("Access outside the allowed workspace is blocked.") from exc

    return requested_path


def read_file(file_path: str | Path, workspace: str | Path | None = None) -> str:
    """Read a UTF-8 text file, optionally enforcing a workspace boundary."""
    path = Path(file_path).resolve()

    if workspace is not None:
        path = _safe_path(workspace, path)

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return path.read_text(encoding="utf-8")
