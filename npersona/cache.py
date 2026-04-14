"""Document profile cache — avoid re-running LLM extraction for the same document."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from npersona.models.profile import SystemProfile

logger = logging.getLogger(__name__)


def _document_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class ProfileCache:
    """In-memory + optional file-backed cache for extracted SystemProfiles."""

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        self._memory: dict[str, SystemProfile] = {}
        self._cache_dir: Path | None = Path(cache_dir) if cache_dir else None
        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, document_text: str) -> SystemProfile | None:
        key = _document_hash(document_text)
        if key in self._memory:
            logger.debug("Profile cache hit (memory): %s", key)
            return self._memory[key]
        if self._cache_dir:
            path = self._cache_dir / f"{key}.json"
            if path.exists():
                logger.debug("Profile cache hit (disk): %s", key)
                try:
                    profile = SystemProfile.model_validate_json(path.read_text())
                    self._memory[key] = profile
                    return profile
                except Exception as exc:
                    logger.warning("Corrupt cache file %s: %s", path, exc)
                    path.unlink(missing_ok=True)
        return None

    def set(self, document_text: str, profile: SystemProfile) -> None:
        key = _document_hash(document_text)
        self._memory[key] = profile
        if self._cache_dir:
            path = self._cache_dir / f"{key}.json"
            try:
                path.write_text(profile.model_dump_json(indent=2))
                logger.debug("Profile cached to disk: %s", path)
            except Exception as exc:
                logger.warning("Failed to write cache file %s: %s", path, exc)

    def clear(self) -> None:
        self._memory.clear()
        if self._cache_dir:
            for f in self._cache_dir.glob("*.json"):
                f.unlink(missing_ok=True)
