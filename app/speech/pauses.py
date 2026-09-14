"""Intelligent contextual pause calculations between speaker turns."""

from typing import Optional
from app.models.ast import DialogueNode, PauseNode, ScriptNode


class PauseCalculator:
    """Calculates natural, conversational pauses between dialogue turns."""

    QUICK_REACTION_WORDS = {
        "yeah", "yes", "right", "exactly", "totally", "sure", "no", "nope",
        "seriously", "wow", "interesting", "agreed", "definitely", "absolutely",
        "indeed", "true", "honestly", "fair", "sounds good", "thanks", "thank you"
    }

    @classmethod
    def is_quick_reaction(cls, text: str) -> bool:
        """Determines if a turn is a brief conversational reaction."""
        clean = text.strip().lower().rstrip(".?!,")
        words = clean.split()
        if len(words) <= 4:
            if clean in cls.QUICK_REACTION_WORDS:
                return True
            if any(w in cls.QUICK_REACTION_WORDS for w in words):
                return True
            if len(words) <= 2:
                return True
        return False

    @classmethod
    def calculate_pause_between(
        cls,
        current_node: ScriptNode,
        next_node: Optional[ScriptNode],
        default_pause_ms: int = 350,
        quick_reaction_ms: int = 200,
        topic_pause_ms: int = 700,
    ) -> int:
        """Determines the natural pause duration in ms following current_node."""
        # If there is no next node, minimal trailing silence
        if next_node is None:
            return 250

        # If next node is an explicit pause, return 0 (the explicit pause will be handled separately)
        if isinstance(next_node, PauseNode) or (isinstance(next_node, dict) and next_node.get("type") == "pause"):
            return 0

        # If current is an explicit pause node, return its duration
        if isinstance(current_node, PauseNode):
            return current_node.duration_ms
        if isinstance(current_node, dict) and current_node.get("type") == "pause":
            return current_node.get("duration_ms", default_pause_ms)

        # Both are dialogue turns
        curr_text = current_node.text if isinstance(current_node, DialogueNode) else current_node.get("text", "")
        next_text = next_node.text if isinstance(next_node, DialogueNode) else next_node.get("text", "")
        curr_speaker = current_node.speaker if isinstance(current_node, DialogueNode) else current_node.get("speaker", "")
        next_speaker = next_node.speaker if isinstance(next_node, DialogueNode) else next_node.get("speaker", "")

        # If next turn is by the same speaker (rare in standard dialogue, but possible)
        if curr_speaker.lower() == next_speaker.lower():
            return 250

        # If next turn is a quick reaction, use a brisk conversational gap (150 - 300 ms)
        if cls.is_quick_reaction(next_text):
            return quick_reaction_ms

        # If current turn ends with a question mark and next turn is an immediate answer
        if curr_text.strip().endswith("?"):
            return int(default_pause_ms * 0.85)

        # If current turn ends with an ellipsis or dash (thought trail)
        if curr_text.strip().endswith("...") or curr_text.strip().endswith("—"):
            return int(default_pause_ms * 1.2)

        # Standard natural conversational speaker turn change (250 - 500 ms)
        return default_pause_ms
