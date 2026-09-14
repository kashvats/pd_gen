"""Tests for TTS providers, mock synthesis, generation engine, and timeline assembly."""

import pytest
import tempfile
from pathlib import Path

from app.models.project import Project, SpeakerProfile
from app.tts.registry import tts_registry
from app.tts.base import SynthesisRequest, SynthesisResult
from app.audio.generator import AudioGenerationEngine
from app.audio.assembler import TimelineAssembler
from app.projects.manager import ProjectManager


def test_mock_provider_synthesis(mock_engine):
    provider = tts_registry.get("mock")
    assert provider is not None
    assert provider.is_configured()

    req = SynthesisRequest(
        text="Welcome to the podcast. Today we talk about AI.",
        voice_id="mock_host_voice",
        provider="mock",
        speed=1.0,
        studio_mode=True,
    )
    res: SynthesisResult = provider.synthesize(req)
    assert res.audio_bytes is not None
    assert len(res.audio_bytes) > 1000
    assert res.duration_ms > 500


def test_full_project_generation_and_assembly(mock_engine):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mgr = ProjectManager(root_dir=tmp_path / "projects")

        script = """Host: Welcome to Episode 1.
Guest: Thanks for having me!
Host: Let's discuss speech prosody.
"""
        project = mgr.create_project("Test Episode", script)
        # Configure speakers to use mock provider for test
        for sp in project.speakers.values():
            sp.provider = "mock"

        p_dir = mgr.get_project_dir(project.id)
        engine = AudioGenerationEngine(cache_dir=tmp_path / "cache")
        success = engine.generate_project(project, p_dir)
        assert success is True

        # Verify all turns have generated takes
        for node in project.script_nodes:
            if node.get("type") == "dialogue":
                gen_info = project.segments_generation.get(node["id"])
                assert gen_info is not None
                assert gen_info.active_take is not None
                assert Path(gen_info.active_take.audio_path).exists()

        # Assemble timeline
        manifest = TimelineAssembler.assemble(project, p_dir)
        assert manifest is not None
        assert manifest.total_duration_ms > 1000
        assert project.final_audio_path is not None
        assert Path(project.final_audio_path).exists()
