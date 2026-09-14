import io
import subprocess
import sys
import types
import wave
from pathlib import Path
import numpy as np
import pytest
from app.audio.generator import AudioGenerationEngine
from app.audio.assembler import TimelineAssembler
from app.audio.ffmpeg_utils import FFmpegAudioEngine
from app.config.settings import Settings
from app.models.project import Project, SpeakerProfile
from app.models.ast import DialogueNode
from app.parser.markdown_parser import MarkdownScriptParser
from app.parser.text_cleaner import clean_text_for_speech
from app.projects.manager import ProjectManager
from app.voices.library import VoiceLibrary
from app.tts.registry import tts_registry
from app.tts.base import SynthesisRequest
from app.tts.kokoro_provider import KokoroProvider
from app.tts.edge_provider import EdgeTTSProvider


def test_words_links_brackets_and_punctuation_preserved():
    script = 'Teacher: Open the [guide](https://example.com). Use [x] — not **y**.\n\nKeep this sentence.'
    nodes = MarkdownScriptParser.parse(script)
    assert len(nodes) == 1
    assert clean_text_for_speech(nodes[0].text) == 'Open the guide. Use [x] — not y. Keep this sentence.'


def test_neural_adapter_receives_entire_turn_and_actual_duration(monkeypatch):
    engine = KokoroProvider()
    calls = []
    def create(text, **kwargs):
        calls.append((text, kwargs))
        return np.full(24000, 0.1), 24000
    engine._engine = types.SimpleNamespace(create=create)
    monkeypatch.setattr(engine, 'load', lambda: None)
    text = 'Really? I had no idea. Tell me more.'
    result = engine.synthesize(SynthesisRequest(text, 'af_heart', 'kokoro'))
    assert calls[0][0] == text
    assert result.duration_ms == 1000
    assert result.audio_bytes[:4] == b'RIFF'


def test_neural_adapter_rejects_silent_model_output(monkeypatch):
    engine = KokoroProvider()
    engine._engine = types.SimpleNamespace(create=lambda *a, **k: (np.zeros(24000), 24000))
    monkeypatch.setattr(engine, 'load', lambda: None)
    with pytest.raises(RuntimeError, match='silent'):
        engine.synthesize(SynthesisRequest('Hello', 'af_heart', 'kokoro'))


def test_missing_model_never_downloads(monkeypatch, tmp_path):
    engine = KokoroProvider()
    monkeypatch.setattr(engine, 'paths', lambda: (tmp_path/'missing.onnx', tmp_path/'missing.bin'))
    with pytest.raises(RuntimeError, match='not installed'):
        engine.synthesize(SynthesisRequest('Hello', 'af_heart', 'kokoro'))


def test_edge_failure_and_permission_do_not_fallback(monkeypatch):
    calls = []
    def fail(**kwargs):
        calls.append(kwargs)
        raise ValueError('service unavailable')
    monkeypatch.setitem(sys.modules, 'edge_tts', types.SimpleNamespace(Communicate=fail))
    engine = EdgeTTSProvider()
    request = SynthesisRequest('Hello', 'en-US-GuyNeural', 'edge_tts')
    with pytest.raises(RuntimeError, match='permission'):
        engine.synthesize(request)
    assert not calls
    request.settings['allow_online'] = True
    with pytest.raises(RuntimeError, match='service unavailable'):
        engine.synthesize(request)
    assert calls[0]['pitch'] == '+0Hz'
    assert calls[0]['text'] == 'Hello'


def make_project(tmp_path, script):
    manager = ProjectManager(tmp_path/'projects', VoiceLibrary(tmp_path/'voices'))
    project = manager.create_project('test', script)
    return manager, project


def test_failure_blocks_partial_export(tmp_path, monkeypatch, mock_engine):
    manager, project = make_project(tmp_path, 'A: First.\nB: Second.')
    project.speakers['A'].provider = 'mock'
    project.speakers['B'].provider = 'not_installed'
    engine = AudioGenerationEngine(cache_dir=tmp_path/'cache')
    assert not engine.generate_project(project, manager.get_project_dir(project.id))
    assert next(iter(project.segments_generation.values())).active_take
    with pytest.raises(RuntimeError, match='Missing or failed'):
        TimelineAssembler.assemble(project, manager.get_project_dir(project.id))


def test_explicit_pause_is_not_doubled_and_leading_pause_survives(tmp_path, mock_engine):
    manager, project = make_project(tmp_path, '[PAUSE: 100ms]\nA: First.\n[PAUSE: 500ms]\nB: Second.')
    for profile in project.speakers.values():
        profile.provider = 'mock'
    project.settings.output_format = 'wav'
    engine = AudioGenerationEngine(cache_dir=tmp_path/'cache')
    directory = manager.get_project_dir(project.id)
    assert engine.generate_project(project, directory)
    first = next(n for n in project.script_nodes if n['type'] == 'dialogue')
    assert project.segments_generation[first['id']].calculated_pause_after_ms == 0
    manifest = TimelineAssembler.assemble(project, directory)
    assert manifest.items[0].duration_ms == 100
    actual = FFmpegAudioEngine.get_duration_ms(manifest.final_audio_path)
    assert abs(actual - manifest.total_duration_ms) < 5


def test_unchanged_ids_and_plan_survive_edit(tmp_path, mock_engine):
    manager, project = make_project(tmp_path, 'A: Keep this.\nB: Change that.')
    for profile in project.speakers.values(): profile.provider = 'mock'
    original = project.script_nodes[0]['id']
    engine = AudioGenerationEngine(cache_dir=tmp_path/'cache')
    assert engine.generate_project(project, manager.get_project_dir(project.id))
    manager.sync_markdown_to_project(project, 'A: Keep this.\nB: Changed that.')
    assert project.script_nodes[0]['id'] == original
    assert engine.plan_generation(project).cached_turns == 1


def tone(path, rate):
    data = (np.sin(np.arange(rate)*2*np.pi*300/rate)*5000).astype('<i2')
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate); f.writeframes(data.tobytes())


def test_mixed_mp3_wav_and_rates_have_correct_duration(tmp_path):
    a, b = tmp_path/'a.wav', tmp_path/'b.wav'
    tone(a, 24000); tone(b, 48000)
    mp3 = tmp_path/'b.mp3'
    subprocess.run([Settings.find_ffmpeg(), '-y', '-loglevel', 'error', '-i', str(b), str(mp3)], check=True)
    output = tmp_path/'final.wav'
    assert FFmpegAudioEngine.assemble_timeline([(str(a), 300), (str(mp3), 0)], output,
                                               normalize=False, output_format='wav')
    assert abs(FFmpegAudioEngine.get_duration_ms(str(output)) - 2300) < 10


def test_missing_ffmpeg_does_not_create_fake_mp3(tmp_path, monkeypatch):
    source = tmp_path/'a.wav'; tone(source, 24000)
    monkeypatch.setattr(Settings, 'find_ffmpeg', lambda: None)
    with pytest.raises(RuntimeError, match='Install FFmpeg'):
        FFmpegAudioEngine.assemble_timeline([(str(source), 0)], tmp_path/'out.mp3')
    assert not (tmp_path/'out.mp3').exists()
    assert not (tmp_path/'out.wav').exists()


def test_dynamic_speakers_get_distinct_neural_voices(tmp_path):
    _, project = make_project(tmp_path, 'Host: Hello.\nAI: Hi.\nRobot: Welcome.')
    voices = [p.voice_id for p in project.speakers.values()]
    assert len(set(voices)) == 3
    assert all(p.provider == 'kokoro' and p.preset != 'Robotic AI' for p in project.speakers.values())


def test_offline_project_rejects_online_before_network(tmp_path, monkeypatch):
    manager, project = make_project(tmp_path, 'Host: Hello.')
    project.speakers['Host'].provider = 'edge_tts'
    def forbidden(*args):
        pytest.fail('Unexpected network synthesis')
    monkeypatch.setattr(tts_registry.get('edge_tts'), 'synthesize', forbidden)
    assert not AudioGenerationEngine(cache_dir=tmp_path/'cache').generate_project(project, manager.get_project_dir(project.id))
    assert 'disabled' in next(iter(project.segments_generation.values())).error_message
