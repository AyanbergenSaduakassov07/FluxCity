"""Content-addressed artifact store: data/artifacts/<sha[:2]>/<sha>."""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path

from fluxcity.core.errors import InvalidInput, NotFound
from fluxcity.core.hashing import SHA256_RE

_CHUNK = 1 << 20


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _target(self, sha: str) -> Path:
        if not SHA256_RE.match(sha):  # rejects "../", absolute paths, anything not a digest
            raise InvalidInput("bad_sha", f"not a sha256 digest: {sha!r}")
        return self.root / sha[:2] / sha

    def put(self, src: Path | bytes) -> str:
        digest = hashlib.sha256()
        fd, tmp_name = tempfile.mkstemp(dir=self.root, prefix=".tmp-")
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as out:
                if isinstance(src, bytes):
                    digest.update(src)
                    out.write(src)
                else:
                    with src.open("rb") as f:
                        while chunk := f.read(_CHUNK):
                            digest.update(chunk)
                            out.write(chunk)
            sha = digest.hexdigest()
            target = self._target(sha)
            target.parent.mkdir(exist_ok=True)
            if target.exists():
                tmp.unlink()
            else:
                shutil.move(tmp, target)
            return sha
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    def path(self, sha: str) -> Path:
        target = self._target(sha)
        if not target.exists():
            raise NotFound("artifact_missing", f"artifact {sha} not found")
        return target
