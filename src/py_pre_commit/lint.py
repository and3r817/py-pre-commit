import subprocess
from collections.abc import Callable

WHOLE_PROJECT: tuple[tuple[str, ...], ...] = (
    ("ruff", "check", "--fix", "--exit-non-zero-on-fix", "."),
    ("ruff", "format", "."),
    ("uv", "lock", "--check"),
)

HYGIENE: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("check-yaml", "--unsafe"), ("*.yaml", "*.yml")),
    (("check-toml",), ("*.toml",)),
    (("check-merge-conflict",), ()),
    (("check-added-large-files", "--maxkb=500"), ()),
    (("detect-private-key",), ()),
    (("trailing-whitespace-fixer", "--markdown-linebreak-ext=md"), ()),
    (("end-of-file-fixer",), ()),
    (("debug-statement-hook",), ("*.py",)),
)


def steps(resolve: Callable[[tuple[str, ...]], list[str]]) -> list[tuple[str, ...]]:
    commands = list(WHOLE_PROJECT)
    for cmd, globs in HYGIENE:
        files = resolve(globs)
        if files:
            commands.append((*cmd, *files))
    return commands


def _tracked(globs: tuple[str, ...]) -> list[str]:
    completed = subprocess.run(
        ("git", "ls-files", "-z", *globs), capture_output=True, text=True, check=True
    )
    return [path for path in completed.stdout.split("\0") if path]


def main() -> int:
    return max(subprocess.run(cmd).returncode for cmd in steps(_tracked))
