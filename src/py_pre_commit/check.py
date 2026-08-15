import subprocess
from collections.abc import Sequence
from pathlib import Path

DEPTRY_IGNORES = "DEP002=uvicorn"
VULTURE_EXCLUDE = "**/tests/**,**/.venv/**"


def steps(members: Sequence[tuple[str, str]]) -> list[tuple[str, ...]]:
    return [
        ("uv", "run", "ty", "check"),
        (
            "uv",
            "run",
            "vulture",
            *(f"{directory}/src" for directory, _ in members),
            "--exclude",
            VULTURE_EXCLUDE,
            "--min-confidence",
            "80",
            "--sort-by-size",
        ),
        *(
            (
                "uv",
                "run",
                "--directory",
                directory,
                "deptry",
                "src",
                "--known-first-party",
                package,
                "--per-rule-ignores",
                DEPTRY_IGNORES,
            )
            for directory, package in members
        ),
    ]


def _members() -> list[tuple[str, str]]:
    return sorted(
        (path.parent.name, next(child.name for child in sorted(path.iterdir()) if child.is_dir()))
        for path in Path().glob("*/src")
    )


def main() -> int:
    return max(subprocess.run(cmd).returncode for cmd in steps(_members()))
