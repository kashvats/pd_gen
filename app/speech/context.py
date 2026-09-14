"""Multi-turn conversational context builder for intelligent speech synthesis."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from app.models.ast import DialogueNode, ScriptNode


@dataclass
class DialogueContextWindow:
    """Surrounding conversational context for a single dialogue turn."""
    turn_index: int
    total_turns: int
    current_speaker: str
    current_text: str
    previous_speaker: Optional[str] = None
    previous_text: Optional[str] = None
    next_speaker: Optional[str] = None
    next_text: Optional[str] = None
    directives: Dict[str, Any] = None

    def __post_init__(self):
        if self.directives is None:
            self.directives = {}


def build_context_windows(nodes: List[ScriptNode]) -> List[DialogueContextWindow]:
    """Extracts sliding context windows for all dialogue nodes in a script."""
    dialogue_nodes: List[DialogueNode] = []
    for node in nodes:
        if isinstance(node, DialogueNode):
            dialogue_nodes.append(node)
        elif isinstance(node, dict) and node.get("type") == "dialogue":
            dialogue_nodes.append(DialogueNode.from_dict(node))

    total = len(dialogue_nodes)
    windows: List[DialogueContextWindow] = []

    for i, curr in enumerate(dialogue_nodes):
        prev_node = dialogue_nodes[i - 1] if i > 0 else None
        next_node = dialogue_nodes[i + 1] if i < total - 1 else None

        windows.append(
            DialogueContextWindow(
                turn_index=i,
                total_turns=total,
                current_speaker=curr.speaker,
                current_text=curr.text,
                previous_speaker=prev_node.speaker if prev_node else None,
                previous_text=prev_node.text if prev_node else None,
                next_speaker=next_node.speaker if next_node else None,
                next_text=next_node.text if next_node else None,
                directives=curr.directives,
            )
        )

    return windows
