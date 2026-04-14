"""Tests for ProfileCache."""

import tempfile
from pathlib import Path

import pytest

from npersona.cache import ProfileCache
from npersona.models.profile import Agent, SystemProfile


def _make_profile(name: str = "Test AI") -> SystemProfile:
    return SystemProfile(
        system_name=name,
        system_description="A test AI system.",
        agents=[Agent(id="bot", name="Support Bot", description="Answers questions.")],
    )


class TestProfileCache:
    def test_miss_returns_none(self):
        cache = ProfileCache()
        assert cache.get("some document text") is None

    def test_set_and_get_in_memory(self):
        cache = ProfileCache()
        profile = _make_profile()
        cache.set("my document", profile)
        retrieved = cache.get("my document")
        assert retrieved is not None
        assert retrieved.system_name == "Test AI"

    def test_different_documents_get_different_entries(self):
        cache = ProfileCache()
        cache.set("doc A", _make_profile("System A"))
        cache.set("doc B", _make_profile("System B"))
        assert cache.get("doc A").system_name == "System A"
        assert cache.get("doc B").system_name == "System B"

    def test_same_document_different_content_is_miss(self):
        cache = ProfileCache()
        cache.set("document one", _make_profile())
        assert cache.get("document two") is None

    def test_clear_removes_all_entries(self):
        cache = ProfileCache()
        cache.set("doc", _make_profile())
        cache.clear()
        assert cache.get("doc") is None

    def test_disk_cache_persists_and_reloads(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache1 = ProfileCache(cache_dir=tmp_dir)
            cache1.set("persistent document", _make_profile("Persisted System"))

            # New cache instance — cold memory, warm disk
            cache2 = ProfileCache(cache_dir=tmp_dir)
            retrieved = cache2.get("persistent document")

            assert retrieved is not None
            assert retrieved.system_name == "Persisted System"

    def test_disk_cache_creates_json_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = ProfileCache(cache_dir=tmp_dir)
            cache.set("some document content", _make_profile())
            json_files = list(Path(tmp_dir).glob("*.json"))
            assert len(json_files) == 1

    def test_corrupt_cache_file_falls_back_to_miss(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = ProfileCache(cache_dir=tmp_dir)
            doc = "document with corrupt cache"
            cache.set(doc, _make_profile())

            # Corrupt the cache file
            json_files = list(Path(tmp_dir).glob("*.json"))
            json_files[0].write_text("{ this is not valid json }")

            # Clear memory so it must read from disk
            cache._memory.clear()

            # Should return None gracefully, not raise
            result = cache.get(doc)
            assert result is None
