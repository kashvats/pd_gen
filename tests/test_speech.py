"""Tests for Speech Director, context windows, pauses, and pronunciation engine."""

import pytest
from app.models.ast import DialogueNode
from app.models.project import SpeakerProfile
from app.speech.context import build_context_windows
from app.speech.director import SpeechDirector
from app.speech.pauses import PauseCalculator
from app.speech.pronunciation import PronunciationEngine


def test_context_window_builder():
    nodes = [
        DialogueNode(speaker="Host", text="Question 1?", order=0),
        DialogueNode(speaker="Guest", text="Answer 1.", order=1),
        DialogueNode(speaker="Host", text="Follow up?", order=2),
    ]
    windows = build_context_windows(nodes)
    assert len(windows) == 3
    assert windows[0].previous_speaker is None
    assert windows[0].next_speaker == "Guest"
    assert windows[1].previous_speaker == "Host"
    assert windows[1].next_speaker == "Host"
    assert windows[2].previous_speaker == "Guest"
    assert windows[2].next_speaker is None


def test_speech_director_cues():
    nodes = [
        DialogueNode(speaker="Host", text="You built it all in one weekend?", order=0),
        DialogueNode(speaker="Guest", text="Yeah. Seriously.", order=1),
        DialogueNode(speaker="Host", text="Seriously?! That is insane.", order=2),
    ]
    windows = build_context_windows(nodes)

    cue0 = SpeechDirector.infer_conversational_cue(windows[0])
    assert "question" in cue0.lower() or "curious" in cue0.lower()

    cue1 = SpeechDirector.infer_conversational_cue(windows[1])
    assert "agreement" in cue1.lower() or "natural" in cue1.lower()

    cue2 = SpeechDirector.infer_conversational_cue(windows[2])
    assert "surprise" in cue2.lower()


def test_speech_director_preserves_dialogue_text():
    # Verify that direction composition generates instruction metadata without altering dialogue
    nodes = [DialogueNode(speaker="Host", text="What did you do next?", order=0)]
    windows = build_context_windows(nodes)
    prof = SpeakerProfile(name="Host", direction_prompt="Warm and confident.")

    instruction = SpeechDirector.compose_delivery_instruction(windows[0], prof, studio_mode=True)
    assert "Warm and confident" in instruction
    assert windows[0].current_text == "What did you do next?"  # Original text strictly intact


def test_pause_calculator():
    node1 = DialogueNode(speaker="Host", text="Did you enjoy it?", order=0)
    node2 = DialogueNode(speaker="Guest", text="Exactly.", order=1)
    node3 = DialogueNode(speaker="Host", text="Tell us more about the architecture.", order=2)

    # Quick reaction node2 should yield short pause (e.g. ~200ms)
    pause_to_reaction = PauseCalculator.calculate_pause_between(node1, node2)
    assert pause_to_reaction == 200

    # Normal turn node2 -> node3
    pause_normal = PauseCalculator.calculate_pause_between(node2, node3)
    assert pause_normal == 350


def test_pronunciation_engine_substitution():
    text = "We built the OpenAI integration using SQL and a clean UI."
    replaced = PronunciationEngine.apply_substitutions(
        text,
        project_dict={"UI": "user interface"},
        speaker_dict={"SQL": "S.Q.L."},
    )
    assert "Open A.I." in replaced
    assert "S.Q.L." in replaced
    assert "user interface" in replaced
