import subprocess
import sys
from pathlib import Path


def run_tests(
    workspace: str | Path,
) -> tuple[bool, str]:

    workspace = Path(workspace).resolve()

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
            ],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60,
        )

    except subprocess.TimeoutExpired:

        return False, "Tests timed out after 60 seconds."

    except Exception as exc:

        return False, f"Could not run tests: {exc}"

    output = "\n".join(
        part
        for part in [
            result.stdout,
            result.stderr,
        ]
        if part
    )

    return (
        result.returncode == 0,
        output,
    )