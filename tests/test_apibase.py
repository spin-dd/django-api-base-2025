"""Tests for the `apibase` package surface."""

from pathlib import Path

from apibase import __version__

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _declared_version() -> str:
    """pyproject の [project] version を読む (tomllib は 3.11+ なので使わない)."""
    in_project = False
    for line in PYPROJECT.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_project = stripped == "[project]"
            continue
        if in_project and stripped.startswith("version"):
            return stripped.split("=", 1)[1].strip().strip('"')
    raise AssertionError("pyproject.toml の [project] に version が無い")


def test_version_comes_from_the_installed_distribution():
    """`__version__` は配布メタデータ由来で、pyproject の version と一致する。

    版の文字列を 2 箇所に持つと release のたびに片方が取り残される
    (pyproject が 0.4.5 になっても `__init__` は 0.4.0 のままだった)。
    ここが落ちたら、pyproject を上げたあと再インストールしていない疑い
    (editable でもメタデータは install 時に書かれる)。
    """
    assert __version__ == _declared_version()
