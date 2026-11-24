import subprocess
import sys
from pathlib import Path

import fluxcity


def test_package_imports() -> None:
    assert fluxcity.__version__


def test_libsumo_imports() -> None:
    import libsumo

    assert hasattr(libsumo, "simulation")


def test_sumo_binary_reports_pinned_version() -> None:
    sumo = Path(sys.executable).parent / "sumo"
    out = subprocess.run([str(sumo), "--version"], capture_output=True, text=True, timeout=30)
    assert "1.28.0" in out.stdout
