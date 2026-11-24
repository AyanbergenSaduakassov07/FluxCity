import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_licenses.py"


@pytest.fixture(scope="module")
def cl() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_licenses", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_licenses"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def clean_tree(tmp_path: Path) -> Path:
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "a.py").write_text("x = 1\n")
    (tmp_path / "UPSTREAM.md").write_text(
        "# Upstream\n## Extracted files\n| FluxCity path | Upstream | License | Changes |\n"
        "|---|---|---|---|\n| `backend/ok.py` | repo@1:x.py | MIT | none |\n"
    )
    (tmp_path / "backend" / "ok.py").write_text("# Extracted from: repo@1:x.py\n")
    return tmp_path


def test_clean_tree_passes(cl: ModuleType, clean_tree: Path) -> None:
    assert cl.check_tree(clean_tree) == []


def test_resco_dir_fails(cl: ModuleType, clean_tree: Path) -> None:
    (clean_tree / "vendor" / "nets" / "RESCO").mkdir(parents=True)
    assert any("RESCO" in v for v in cl.check_tree(clean_tree))


def test_undeclared_extract_fails(cl: ModuleType, clean_tree: Path) -> None:
    (clean_tree / "backend" / "stolen.ts").write_text("// Extracted from: other@2:y.ts\n")
    assert cl.check_tree(clean_tree) == [
        "backend/stolen.ts: has 'Extracted from:' header but no UPSTREAM.md row"
    ]


@pytest.mark.parametrize(
    ("expr", "field", "classifiers", "ok"),
    [
        ("MIT", None, [], True),
        ("EPL-2.0 OR GPL-2.0-or-later", None, [], True),  # SUMO: OR picks EPL
        ("GPL-3.0-only", None, [], False),
        ("MIT AND GPL-3.0-only", None, [], False),
        (None, "Apache 2.0", [], True),
        (None, None, ["License :: OSI Approved :: MIT License"], True),
        (None, None, ["License :: OSI Approved :: GNU General Public License v3 (GPLv3)"], False),
        (None, None, [], False),  # no metadata
        ("LGPL-3.0-only", None, [], False),
    ],
)
def test_classify(
    cl: ModuleType, expr: str | None, field: str | None, classifiers: list[str], ok: bool
) -> None:
    assert (cl.classify("pkg", expr, field, classifiers, cl.Policy.load()) is None) is ok


def test_lgpl_needs_exception_and_override_wins(cl: ModuleType) -> None:
    base = cl.Policy.load()
    pol = cl.Policy(base.allowed, base.aliases, {"weird-pkg": "MIT"}, frozenset({"libfoo"}))
    assert cl.classify("libfoo", "LGPL-3.0-only", None, [], pol) is None
    assert cl.classify("Weird_Pkg", None, None, [], pol) is None
