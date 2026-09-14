"""Dynamic detection and extraction of arbitrary speaker names."""

import re
from typing import List, Set
from app.models.ast import DialogueNode


# Pattern matching '<Speaker Name>: <Dialogue>' or '<Speaker Name> [directive]: <Dialogue>'
# Disallows markdown headings like '# Heading', blockquotes '> quote', or list items '- item'
SPEAKER_REGEX = re.compile(
    r'^(?![#>*\-`\d+\.\s])([A-Za-z0-9\s\.\-—\'\(\)]+?)(?:\s*\[([^\]]+)\])?:\s*(.*)$'
)


def detect_speakers(text_or_nodes) -> List[str]:
    """Dynamically detects unique speaker names in order of appearance."""
    speakers_ordered: List[str] = []
    seen: Set[str] = set()

    if isinstance(text_or_nodes, str):
        lines = text_or_nodes.splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue

            match = SPEAKER_REGEX.match(line_str)
            if match:
                speaker = match.group(1).strip()
                if speaker and speaker not in seen:
                    seen.add(speaker)
                    speakers_ordered.append(speaker)
    elif isinstance(text_or_nodes, list):
        for node in text_or_nodes:
            if isinstance(node, DialogueNode):
                speaker = node.speaker.strip()
                if speaker and speaker not in seen:
                    seen.add(speaker)
                    speakers_ordered.append(speaker)
            elif isinstance(node, dict) and node.get("type") == "dialogue":
                speaker = node.get("speaker", "").strip()
                if speaker and speaker not in seen:
                    seen.add(speaker)
                    speakers_ordered.append(speaker)

    return speakers_ordered
