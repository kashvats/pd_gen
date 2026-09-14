"""Context-Aware Speech Director for natural prosody, emotion, and conversational dynamics."""

import re
from typing import Optional, Dict, Any
from app.models.project import SpeakerProfile
from app.speech.context import DialogueContextWindow


class SpeechDirector:
    """Infers conversational prosody, tone, and delivery instructions from context."""

    SURPRISE_TRIGGERS = [
        "seriously", "really", "whoa", "wait", "no way", "unbelievable",
        "insane", "how is that", "you actually", "what happened"
    ]
    FRUSTRATED_TRIGGERS = [
        "come on", "don't do that", "that's cheap", "hate this", "ridiculous",
        "stop taking sides", "not true", "can you let me", "annoying", "manipulative"
    ]
    SKEPTICAL_TRIGGERS = [
        "is it", "probably", "depends", "are you sure", "really", "reassuring", "how so"
    ]
    AMUSED_TRIGGERS = [
        "haha", "hilarious", "funny", "slightly insane", "of course", "lol", "brilliant", "wonderful"
    ]
    AGREEMENT_TRIGGERS = [
        "exactly", "precisely", "totally", "agreed", "fair", "honestly", "sounds good", "correct", "thank you"
    ]
    THOUGHTFUL_TRIGGERS = [
        "i think", "in my view", "the easiest way", "let's consider", "interestingly",
        "fundamentally", "to understand", "the real argument", "for decades", "imagine a future"
    ]

    @classmethod
    def infer_conversational_cue(cls, context: DialogueContextWindow) -> str:
        """Infers the underlying conversational emotion/cue without altering words."""
        text = context.current_text.strip()
        lower = text.lower()

        # 1. Explicit directive in script overrides or seeds inference
        if context.directives and context.directives.get("emotion"):
            return context.directives["emotion"]

        # 2. Check for frustration / defensiveness
        if any(trig in lower for trig in cls.FRUSTRATED_TRIGGERS) or (lower.endswith("!") and any(w in lower for w in ["stop", "cheap", "hate", "no", "not"])):
            return "passionate, frustrated, authentic defensive human emotion"

        # 3. Check for skepticism / irony
        if any(trig in lower for trig in cls.SKEPTICAL_TRIGGERS) or lower.startswith("very "):
            return "skeptical, dry, slightly ironic conversational tone"

        # 4. Check for surprise / disbelief
        if (
            "?!" in lower or
            "!?" in lower or
            (lower.endswith("?") and any(trig in lower for trig in cls.SURPRISE_TRIGGERS)) or
            any(f"{trig}?" in lower or f"{trig}!" in lower or f"{trig}?!" in lower for trig in cls.SURPRISE_TRIGGERS) or
            ("seriously" in lower and ("?" in lower or "!" in lower or "insane" in lower))
        ):
            return "mild genuine surprise and curious reaction"

        # 5. Check for amusement / humor / sarcasm
        if any(trig in lower for trig in cls.AMUSED_TRIGGERS):
            return "amused, smiling tone with natural humor"

        # 6. Check for quick agreement / affirmation
        if any(lower.startswith(trig) or lower == trig for trig in cls.AGREEMENT_TRIGGERS):
            return "grounded, natural agreement and conversational affirmation"

        # 7. Check for questions
        if text.endswith("?"):
            return "engaged, curious question delivery with natural upward inflection"

        # 8. Check for thoughtful explanation
        if any(trig in lower for trig in cls.THOUGHTFUL_TRIGGERS) or len(text.split()) > 20:
            return "clear, thoughtful, contemplative human explanation"

        # 9. Check for exclamation / excitement
        if text.endswith("!"):
            return "enthusiastic, highly engaged conversational delivery"

        return "natural, authentic conversational delivery"


    @classmethod
    def compose_delivery_instruction(
        cls,
        context: DialogueContextWindow,
        speaker_profile: Optional[SpeakerProfile] = None,
        studio_mode: bool = True,
    ) -> str:
        """Composes a holistic voice direction prompt for providers supporting instructions."""
        parts = []

        # Base character direction prompt
        if speaker_profile and speaker_profile.direction_prompt.strip():
            parts.append(speaker_profile.direction_prompt.strip())

        # Inferred conversational cue
        cue = cls.infer_conversational_cue(context)
        parts.append(f"Deliver with {cue}.")

        # In Studio Mode, add contextual awareness
        if studio_mode:
            if context.previous_speaker and context.previous_text:
                prev_snippet = context.previous_text.replace("\n", " ")
                if len(prev_snippet) > 80:
                    prev_snippet = prev_snippet[:77] + "..."
                parts.append(f"Context: Replying to {context.previous_speaker}'s comment: \"{prev_snippet}\".")

            # Prosodic advice
            if context.current_text.endswith("?"):
                parts.append("Ensure realistic upward conversational question lilt.")
            elif context.current_text.endswith("..."):
                parts.append("Gentle trail-off cadence.")

        return " ".join(parts)
