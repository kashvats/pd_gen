"""Tests for Markdown parsing, dynamic speaker detection, and text cleaning."""

import pytest
from app.models.ast import DialogueNode, PauseNode, SoundEffectNode
from app.parser.markdown_parser import MarkdownScriptParser
from app.parser.speaker_detector import detect_speakers
from app.parser.text_cleaner import clean_text_for_speech


def test_dynamic_speaker_detection():
    script = """# Title
Host: Welcome.
Co-Host: Hello there.
Dr. Sarah Lee: Good morning.
Guest 1: Glad to be here.
AI Assistant: Standing by.
"""
    speakers = detect_speakers(script)
    assert speakers == ["Host", "Co-Host", "Dr. Sarah Lee", "Guest 1", "AI Assistant"]


def test_multiline_dialogue_parsing():
    script = """Host: This is the first sentence.
This is the second sentence of the same turn.
And a third one.

Guest: Response from guest.
"""
    nodes = MarkdownScriptParser.parse(script)
    dialogue_nodes = [n for n in nodes if isinstance(n, DialogueNode)]
    assert len(dialogue_nodes) == 2
    assert dialogue_nodes[0].speaker == "Host"
    assert "first sentence" in dialogue_nodes[0].text
    assert "second sentence" in dialogue_nodes[0].text
    assert dialogue_nodes[1].speaker == "Guest"
    assert dialogue_nodes[1].text == "Response from guest."


def test_headings_and_pauses():
    script = """# Episode 1
## Intro
Host: Line 1.

[PAUSE: 1.5s]

Guest: Line 2.
"""
    nodes = MarkdownScriptParser.parse(script)
    assert len(nodes) == 3
    assert isinstance(nodes[0], DialogueNode)
    assert isinstance(nodes[1], PauseNode)
    assert nodes[1].duration_ms == 1500
    assert isinstance(nodes[2], DialogueNode)


def test_speaker_directives():
    script = """Host [excited]: Look at that!
Guest [thoughtful]: Indeed.
"""
    nodes = MarkdownScriptParser.parse(script)
    assert len(nodes) == 2
    assert nodes[0].directives.get("emotion") == "excited"
    assert nodes[1].directives.get("emotion") == "thoughtful"


def test_text_cleaner_for_speech():
    raw = "**Important:** Check this `code` out and [click here](http://example.com) — immediately."
    cleaned = clean_text_for_speech(raw)
    assert "**" not in cleaned
    assert "`" not in cleaned
    assert "http" not in cleaned
    assert "Important: Check this code out and click here — immediately." in cleaned
