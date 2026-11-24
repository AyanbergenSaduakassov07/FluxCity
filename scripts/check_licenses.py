"""ADR-014 license gate: dependency licenses, RESCO nets, undeclared extracted code.

Usage: uv run python scripts/check_licenses.py [--root PATH]
Exits 1 and logs one line per violation.
"""

import argparse
import logging
import re
import sys
import tomllib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from importlib.metadata import distributions
from pathlib import Path

log = logging.getLogger("check_licenses")

CONFIG = Path(__file__).with_name("license_allowlist.toml")
SKIP_DIRS = {".git", ".venv", "node_modules", "discovery", ".mypy_cache", ".ruff_cache"}
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js"}
EXTRACT_MARK = "Extracted from:"
EXTRACT_RE = re.compile(r"^\s*(#|//|/\*|\*)\s*Extracted from:", re.M)  # comment headers only
SELF = Path(__file__).resolve()


@dataclass(frozen=True)
class Policy:
    allowed: frozenset[str]
    aliases: dict[str, str]
    overrides: dict[str, str]
    lgpl_exceptions: frozenset[str]

    @classmethod
    def load(cls, path: Path = CONFIG) -> "Policy":
        cfg = tomllib.loads(path.read_text())
        return cls(
            allowed=frozenset(cfg["allowed"]),
            aliases=dict(cfg.get("aliases", {})),
            overrides=dict(cfg.get("overrides", {})),
            lgpl_exceptions=frozenset(cfg.get("lgpl_exceptions", {})),
        )


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _term_ok(term: str, pkg: str, policy: Policy) -> bool:
    spdx = policy.aliases.get(term, term).strip("() ")
    if spdx in policy.allowed:
        return True
    return spdx.startswith("LGPL") and _norm(pkg) in policy.lgpl_exceptions


def expression_ok(expr: str, pkg: str, policy: Policy) -> bool:
    """SPDX expression: OR = any alternative allowed, AND = all parts allowed."""
    return any(
        all(_term_ok(part.strip(), pkg, policy) for part in re.split(r"\s+AND\s+", alt))
        for alt in re.split(r"\s+OR\s+", expr.strip("() "))
    )


def classify(
    pkg: str,
    expression: str | None,
    license_field: str | None,
    classifiers: Iterable[str],
    policy: Policy,
) -> str | None:
    """Return a violation message, or None when the package's license is allowed."""
    override = policy.overrides.get(_norm(pkg))
    if override:
        candidates = [override]
    elif expression:
        candidates = [expression]
    else:
        trove = [c.split("::")[-1].strip() for c in classifiers if c.startswith("License ::")]
        short = license_field.strip() if license_field and len(license_field) < 80 else None
        candidates = trove or ([short] if short else [])
    if not candidates:
        return f"{pkg}: no license metadata (add a verified override)"
    candidates = [policy.aliases.get(c, c) for c in candidates]
    if any(expression_ok(c, pkg, policy) for c in candidates):
        return None
    return f"{pkg}: license {candidates} not on the allow-list"


def check_dependencies(policy: Policy) -> list[str]:
    out = []
    for dist in distributions():
        md = dist.metadata
        msg = classify(
            md["Name"],
            md.get("License-Expression"),
            md.get("License"),
            md.get_all("Classifier") or [],
            policy,
        )
        if msg:
            out.append(msg)
    return sorted(set(out))


def _walk(root: Path) -> Iterator[Path]:
    for path in root.iterdir():
        if path.name in SKIP_DIRS:
            continue
        yield path
        if path.is_dir() and not path.is_symlink():
            yield from _walk(path)


def declared_extracts(root: Path) -> set[str]:
    upstream = root / "UPSTREAM.md"
    if not upstream.exists():
        return set()
    text = upstream.read_text().split("## Extracted files", 1)[-1]
    return {m.group(1) for m in re.finditer(r"^\|\s*`?([^|`]+?)`?\s*\|", text, re.M)}


def check_tree(root: Path) -> list[str]:
    out, declared = [], declared_extracts(root)
    for path in _walk(root):
        rel = path.relative_to(root).as_posix()
        if re.search(r"(^|/)nets/RESCO(/|$)", rel):
            out.append(f"{rel}: RESCO nets are not licensed for redistribution")
            continue
        if path.suffix not in SOURCE_SUFFIXES or not path.is_file() or path.resolve() == SELF:
            continue
        head = path.read_text(errors="replace")[:2000]
        if EXTRACT_RE.search(head) and rel not in declared:
            out.append(f"{rel}: has '{EXTRACT_MARK}' header but no UPSTREAM.md row")
    return out


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    violations = check_dependencies(Policy.load()) + check_tree(args.root.resolve())
    for v in violations:
        log.error(v)
    if violations:
        return 1
    log.info("license gate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
