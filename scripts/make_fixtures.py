"""Regenerate the synthetic grid fixtures in data/fixtures/ with netgenerate (milliseconds).

Usage: uv run python scripts/make_fixtures.py [--check]
--check regenerates into a temp dir and fails if committed fixtures differ (CI).
"""

import argparse
import filecmp
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

log = logging.getLogger("make_fixtures")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "fixtures"
NETGENERATE = Path(sys.executable).parent / "netgenerate"
GRIDS = {"grid1x1": 1, "grid3x3": 3}  # name -> signalized junctions per side
COMMON = [
    "--grid.length",
    "200",
    "--default.lanenumber",
    "2",
    "--tls.guess",
    "true",
    "--grid.attach-length",
    "200",
    "--no-turnarounds",
    "true",
    "--seed",
    "42",
]


def build(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, n in GRIDS.items():
        path = out_dir / f"{name}.net.xml"
        cmd = [
            str(NETGENERATE),
            "--grid",
            "--grid.number",
            str(n),
            *COMMON,
            "--output-file",
            str(path),
            "--no-warnings",
            "true",
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        # drop the timestamped header line and absolute paths so output is byte-reproducible
        lines = path.read_text().splitlines(keepends=True)
        kept = [ln for ln in lines if not ln.startswith("<!-- generated on")]
        path.write_text("".join(kept).replace(str(out_dir) + "/", ""))
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.check:
        for p in build(OUT):
            log.info("wrote %s", p.relative_to(ROOT))
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        stale = [
            p.name
            for p in build(Path(tmp))
            if not (OUT / p.name).exists() or not filecmp.cmp(p, OUT / p.name, shallow=False)
        ]
    for name in stale:
        log.error("data/fixtures/%s is stale; run scripts/make_fixtures.py", name)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
