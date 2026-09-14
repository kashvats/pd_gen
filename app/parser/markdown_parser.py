"""Parser for Markdown dialogue scripts into structured AST nodes."""

import re
from typing import List, Tuple, Optional, Dict, Any
from app.models.ast import DialogueNode, PauseNode, SoundEffectNode, ScriptNode
from app.parser.speaker_detector import SPEAKER_REGEX

# Regex patterns for inline commands
PAUSE_REGEX = re.compile(r'^\[PAUSE:\s*([\d\.]+)\s*(s|sec|seconds|ms|milliseconds)?\]$', re.IGNORECASE)
SFX_REGEX = re.compile(r'^\[SFX:\s*([^\]]+)\]$', re.IGNORECASE)


class MarkdownScriptParser:
    """Parses multi-speaker dialogue markdown into structured ScriptNode AST."""

    @classmethod
    def parse_pause_duration_ms(cls, val_str: str, unit_str: Optional[str]) -> int:
        try:
            val = float(val_str)
            unit = (unit_str or "s").lower()
            if "ms" in unit or "milli" in unit:
                return int(val)
            return int(val * 1000)
        except Exception:
            return 1000

    @classmethod
    def parse(cls, markdown_text: str) -> List[ScriptNode]:
        nodes: List[ScriptNode] = []
        if not markdown_text:
            return nodes

        lines = markdown_text.splitlines()
        current_speaker: Optional[str] = None
        current_text_lines: List[str] = []
        current_directives: Dict[str, Any] = {}
        current_source_line: int = 1
        order = 0

        def flush_dialogue():
            nonlocal current_speaker, current_text_lines, current_directives, current_source_line, order
            if current_speaker is not None and current_text_lines:
                full_text = "\n".join(current_text_lines).strip()
                if full_text:
                    # Only speaker-label directives are metadata. Preserve inline words/links.
                    clean_text = full_text

                    if clean_text:
                        nodes.append(
                            DialogueNode(
                                speaker=current_speaker,
                                text=clean_text,
                                order=order,
                                directives=dict(current_directives),
                                source_line=current_source_line,
                            )
                        )
                        order += 1
            current_speaker = None
            current_text_lines = []
            current_directives = {}


        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Empty line does not break multiline dialogue, but is preserved
            if not stripped:
                if current_speaker is not None:
                    # Keep paragraph breaks inside turn
                    current_text_lines.append("")
                continue

            # Markdown Headings (# Heading, ## Section) -> flush current dialogue
            if stripped.startswith("#"):
                flush_dialogue()
                continue

            # Explicit Pause command: [PAUSE: 2s]
            pause_match = PAUSE_REGEX.match(stripped)
            if pause_match:
                flush_dialogue()
                duration_ms = cls.parse_pause_duration_ms(
                    pause_match.group(1), pause_match.group(2)
                )
                nodes.append(
                    PauseNode(
                        duration_ms=duration_ms,
                        order=order,
                        reason="explicit",
                    )
                )
                order += 1
                continue

            # Sound Effect command: [SFX: applause]
            sfx_match = SFX_REGEX.match(stripped)
            if sfx_match:
                flush_dialogue()
                nodes.append(
                    SoundEffectNode(
                        name=sfx_match.group(1).strip(),
                        order=order,
                    )
                )
                order += 1
                continue

            # Speaker line: 'Speaker Name: Dialogue' or 'Speaker [excited]: Dialogue'
            speaker_match = SPEAKER_REGEX.match(stripped)
            if speaker_match:
                flush_dialogue()
                speaker_name = speaker_match.group(1).strip()
                directive_raw = speaker_match.group(2)
                dialogue_start = speaker_match.group(3).strip()

                current_speaker = speaker_name
                current_source_line = line_idx
                current_directives = {}
                if directive_raw:
                    current_directives["raw_directive"] = directive_raw.strip()
                    current_directives["emotion"] = directive_raw.strip()

                if dialogue_start:
                    current_text_lines.append(dialogue_start)
                continue

            # If inside an active speaker turn, append continuation line
            if current_speaker is not None:
                current_text_lines.append(stripped)

        # Flush any remaining dialogue at end of file
        flush_dialogue()

        return nodes

    @classmethod
    def nodes_to_markdown(cls, nodes: List[ScriptNode]) -> str:
        """Serializes AST nodes back to a clean Markdown format."""
        lines = []
        for node in nodes:
            if isinstance(node, DialogueNode) or (isinstance(node, dict) and node.get("type") == "dialogue"):
                speaker = node.speaker if isinstance(node, DialogueNode) else node.get("speaker", "")
                text = node.text if isinstance(node, DialogueNode) else node.get("text", "")
                directive = ""
                directives = node.directives if isinstance(node, DialogueNode) else node.get("directives", {})
                if directives and "emotion" in directives:
                    directive = f" [{directives['emotion']}]"

                lines.append(f"{speaker}{directive}: {text}\n")
            elif isinstance(node, PauseNode) or (isinstance(node, dict) and node.get("type") == "pause"):
                duration_ms = node.duration_ms if isinstance(node, PauseNode) else node.get("duration_ms", 1000)
                sec = duration_ms / 1000.0
                if sec == int(sec):
                    lines.append(f"[PAUSE: {int(sec)}s]\n")
                else:
                    lines.append(f"[PAUSE: {sec:.1f}s]\n")
            elif isinstance(node, SoundEffectNode) or (isinstance(node, dict) and node.get("type") == "sound_effect"):
                name = node.name if isinstance(node, SoundEffectNode) else node.get("name", "")
                lines.append(f"[SFX: {name}]\n")

        return "\n".join(lines).strip()
