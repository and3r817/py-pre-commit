from py_pre_commit.lint import steps


def test_whole_project_commands_come_first():
    result = steps(lambda globs, text_only: [])

    assert result == [
        ("ruff", "check", "--fix", "--exit-non-zero-on-fix", "."),
        ("ruff", "format", "."),
        ("uv", "lock", "--check"),
    ]


def test_hygiene_commands_carry_the_resolved_files():
    result = steps(lambda globs, text_only: ["a.py"] if globs == ("*.py",) else [])

    assert ("debug-statement-hook", "a.py") in result


def test_a_hygiene_command_is_skipped_when_nothing_matches():
    result = steps(lambda globs, text_only: [] if globs == ("*.toml",) else ["x"])

    assert not any(cmd[0] == "check-toml" for cmd in result)


def test_the_file_rewriting_commands_ask_for_text_only():
    asked = {}

    def resolve(globs, text_only):
        asked[globs, text_only] = True
        return ["a.txt"] if text_only else []

    result = steps(resolve)

    assert ("end-of-file-fixer", "a.txt") in result
    assert ("trailing-whitespace-fixer", "--markdown-linebreak-ext=md", "a.txt") in result
    assert not any(cmd[0] == "check-added-large-files" for cmd in result)
