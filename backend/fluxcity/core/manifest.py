"""Build the reproducibility manifest for a run (SYSTEM_ARCHITECTURE §4)."""

import logging
import platform
import subprocess
import sys

from fluxcity import __version__
from fluxcity.core.models import RunManifest

log = logging.getLogger(__name__)


def git_state() -> tuple[str | None, bool | None]:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=5
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True, timeout=5
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        log.warning("git state unavailable: %s", e)
        return None, None
    return sha, bool(dirty)


def build_manifest(
    *,
    run_id: str,
    scenario_version_hash: str,
    inputs: dict[str, str],
    seed: int,
    sumo_version: str,
    sumo_args: tuple[str, ...],
) -> RunManifest:
    sha, dirty = git_state()
    return RunManifest(
        run_id=run_id,
        scenario_version_hash=scenario_version_hash,
        inputs=inputs,
        seed=seed,
        sumo_version=sumo_version,
        fluxcity_version=__version__,
        git_sha=sha,
        git_dirty=dirty,
        sumo_args=sumo_args,
        platform=platform.platform(),
        python=sys.version.split()[0],
    )
