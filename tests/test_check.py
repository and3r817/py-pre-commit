from py_pre_commit.check import steps


MEMBERS = [("alpha", "alpha_pkg"), ("beta", "beta_pkg")]


def test_ty_runs_once_for_the_whole_workspace():
    result = steps(MEMBERS)

    assert result[0] == ("uv", "run", "ty", "check")


def test_vulture_receives_every_member_src():
    result = steps(MEMBERS)

    assert result[1][:5] == ("uv", "run", "vulture", "alpha/src", "beta/src")


def test_deptry_runs_once_per_member():
    result = steps(MEMBERS)
    deptry = [cmd for cmd in result if "deptry" in cmd]

    assert len(deptry) == 2
    assert deptry[0][:6] == ("uv", "run", "--directory", "alpha", "deptry", "src")


def test_deptry_declares_the_member_package_as_first_party():
    result = steps(MEMBERS)
    deptry = [cmd for cmd in result if "deptry" in cmd]

    assert deptry[0][6:8] == ("--known-first-party", "alpha_pkg")
    assert deptry[1][6:8] == ("--known-first-party", "beta_pkg")
