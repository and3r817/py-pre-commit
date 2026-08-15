import subprocess
from collections.abc import Callable
from fnmatch import fnmatch

from identify.identify import tags_from_path

WHOLE_PROJECT: tuple[tuple[str, ...], ...] = (
    ("ruff", "check", "--fix", "--exit-non-zero-on-fix", "."),
    ("ruff", "format", "."),
    ("uv", "lock", "--check"),
)

HYGIENE: tuple[tuple[tuple[str, ...], tuple[str, ...], bool], ...] = (
    (("check-yaml", "--unsafe"), ("*.yaml", "*.yml"), False),
    (("check-toml",), ("*.toml",), False),
    (("check-merge-conflict",), (), True),
    (("check-added-large-files", "--maxkb=500"), (), False),
    (("detect-private-key",), (), True),
    (("trailing-whitespace-fixer", "--markdown-linebreak-ext=md"), (), True),
    (("end-of-file-fixer",), (), True),
    (("debug-statement-hook",), ("*.py",), False),
)

BINARY_VISIBLE = frozenset({"check-added-large-files"})


def steps(resolve: Callable[[tuple[str, ...], bool], list[str]]) -> list[tuple[str, ...]]:
    commands = list(WHOLE_PROJECT)
    for cmd, globs, text_only in HYGIENE:
        files = resolve(globs, text_only)
        if files:
            commands.append((*cmd, *files))
    return commands


def _tracked() -> list[str]:
    completed = subprocess.run(
        ("git", "ls-files", "-z"), capture_output=True, text=True, check=True
    )
    return [path for path in completed.stdout.split("\0") if path]


def _resolver() -> Callable[[tuple[str, ...], bool], list[str]]:
    tracked = _tracked()
    text = {path for path in tracked if "text" in tags_from_path(path)}

    def resolve(globs: tuple[str, ...], text_only: bool) -> list[str]:
        paths = tracked
        if globs:
            paths = [
                path for path in paths if any(fnmatch(path, glob) for glob in globs)
            ]
        if text_only:
            paths = [path for path in paths if path in text]
        return paths

    return resolve


def main() -> int:
    return max(subprocess.run(cmd).returncode for cmd in steps(_resolver()))
