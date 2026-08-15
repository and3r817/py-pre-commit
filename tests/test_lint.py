from py_pre_commit.lint import steps


def test_whole_project_commands_come_first():
    result = steps(lambda globs: [])

    assert result == [
        ("ruff", "check", "--fix", "--exit-non-zero-on-fix", "."),
        ("ruff", "format", "."),
        ("uv", "lock", "--check"),
    ]


def test_hygiene_commands_carry_the_resolved_files():
    result = steps(lambda globs: ["a.py"] if globs == ("*.py",) else [])

    assert ("debug-statement-hook", "a.py") in result


def test_a_hygiene_command_is_skipped_when_nothing_matches():
    result = steps(lambda globs: [] if globs == ("*.toml",) else ["x"])

    assert not any(cmd[0] == "check-toml" for cmd in result)
