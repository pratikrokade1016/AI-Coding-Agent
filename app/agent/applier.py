from pathlib import Path


def _safe_path(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    path = (root / relative_path).resolve()

    try:
        path.relative_to(root)
    except ValueError as exc:
        raise PermissionError(
            f"Blocked path outside workspace: {relative_path}"
        ) from exc

    return path


def apply_file_change(
    workspace: str | Path,
    operation: str,
    path: str,
    content: str | None = None,
) -> str:

    root = Path(workspace).resolve()
    target = _safe_path(root, path)

    operation = operation.lower()

    if operation == "create":

        if target.exists():
            raise FileExistsError(
                f"Cannot create existing file: {path}"
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content or "",
            encoding="utf-8",
        )

    elif operation == "modify":

        if not target.exists():
            raise FileNotFoundError(
                f"Cannot modify missing file: {path}"
            )

        target.write_text(
            content or "",
            encoding="utf-8",
        )

    elif operation == "delete":

        if not target.exists():
            raise FileNotFoundError(
                f"Cannot delete missing file: {path}"
            )

        target.unlink()

    else:
        raise ValueError(
            f"Unsupported operation: {operation}"
        )

    return str(target.relative_to(root))


def apply_unified_diff(
    workspace: str | Path,
    patch: str,
) -> list[str]:
    """
    Kept for compatibility with the existing agent.

    Unified-diff application is intentionally delegated to
    the higher-level file operation flow.
    """

    raise NotImplementedError(
        "Use apply_file_change() for generated agent changes."
    )