# Markdown Script Format

## Goal

Keep the authoring format simple enough to write by hand while allowing future speech and production directives.

The original Markdown remains a normal editable `.md` file.

---

# Basic dialogue

Primary syntax:

```md
Speaker Name: Dialogue
```

Example:

```md
Host: Welcome back to the show.

Co-Host: Thanks. It's good to be here.

Guest: Thanks for inviting me.
```

---

# Dynamic speaker names

Speaker names are discovered from the script.

Valid examples:

```md
Alex: Hello.

Sarah Connor: Hi.

Co-Host: Welcome.

Guest 1: Thanks.

Dr. Lee: Good morning.

John O'Brien: Nice to meet you.

AI Assistant: How can I help?
```

Do not hard-code a list of allowed characters.

---

# Multiline dialogue

A speaker turn may continue over several lines.

```md
Host: Welcome back to the show.
Today we're talking about local AI,
voice cloning, and natural speech generation.

Guest: Sounds good.
```

This is two speaker turns.

The Host text includes all continuation lines until another recognized structural node begins.

---

# Markdown headings

Markdown headings are document structure, not characters.

```md
# Episode 8

## Introduction

Host: Welcome.

## Main Discussion

Guest: Thanks for having me.
```

Do not detect:

```txt
Episode 8
Introduction
Main Discussion
```

as speakers.

---

# Blank lines

Blank lines do not create dialogue segments.

```md
Host: Hello.


Guest: Hi.
```

This creates exactly two dialogue turns.

---

# Ordering

Script order is authoritative.

```md
A: One.

B: Two.

A: Three.
```

Parsed order:

```txt
1 A
2 B
3 A
```

Generation may finish in another order internally, but assembly must always follow script order.

---

# Speaker parsing rules

A line should be treated as a speaker declaration only when it reasonably matches:

```txt
Speaker Name: optional dialogue
```

The parser should avoid false positives such as:

```txt
https://example.com
12:30
Key: Value
```

when those lines are clearly ordinary Markdown/content rather than dialogue.

Recommended safeguards:

- speaker name should be reasonably short
- speaker name should not start with Markdown heading syntax
- allow letters, numbers, spaces, periods, apostrophes, hyphens and similar name punctuation
- use surrounding script context
- once a name has been recognized as a speaker, later occurrences become stronger matches

Do not make the regex so broad that every colon becomes dialogue.

---

# Empty speaker declaration

Allow:

```md
Host:
Welcome back to the show.
This line is still part of Host's turn.

Guest:
Thanks.
```

---

# Explicit pause

Supported directive:

```md
[PAUSE: 2s]
```

Examples:

```md
Host: And that's when everything changed.

[PAUSE: 1.5s]

Guest: Exactly.
```

Accepted time units can include:

```txt
ms
s
```

Internal representation:

```json
{
  "type": "pause",
  "duration_ms": 1500
}
```

---

# Optional local sound effect

Planned syntax:

```md
[SFX: applause]
```

or later:

```md
[SFX: assets/applause.wav]
```

Sound effects should resolve to local files/library entries by default.

This can be implemented after the core TTS pipeline.

---

# Speaker delivery directive

Planned syntax:

```md
Host [excited]: Welcome back!

Guest [calm]: Thanks for having me.

Narrator [quiet]: Something was about to change.
```

The text inside brackets is delivery metadata.

It must not be spoken.

Internal representation:

```json
{
  "type": "dialogue",
  "speaker": "Host",
  "text": "Welcome back!",
  "directives": {
    "style": "excited"
  }
}
```

---

# Multiple directives

Future syntax may allow:

```md
Host [curious, slower]: Are you sure?
```

Keep the parser extensible rather than hard-coding a tiny list forever.

Unsupported directives should produce a clear warning rather than corrupting the script.

---

# Pronunciation

Pronunciation should primarily live in project/global dictionaries rather than clutter normal Markdown.

A future explicit directive may be supported, but it is not required for the MVP.

---

# Comments / non-spoken notes

A future syntax can support production notes that are not spoken.

Until formally defined, ordinary Markdown comments/content should not automatically become speech.

---

# Text preparation

When converting a dialogue turn to synthesis text:

- remove speaker labels
- remove speech directives
- avoid speaking Markdown formatting markers
- preserve punctuation useful for prosody
- preserve the actual words
- never silently rewrite dialogue

Example:

```md
Host: **This is important.** Are you sure?
```

Spoken text:

```txt
This is important. Are you sure?
```

---

# Internal AST

Recommended:

```python
ScriptNode = DialogueNode | PauseNode | SoundEffectNode | NoteNode
```

Dialogue:

```python
@dataclass
class DialogueNode:
    id: str
    order: int
    speaker: str
    text: str
    directives: dict
```

Pause:

```python
@dataclass
class PauseNode:
    id: str
    order: int
    duration_ms: int
```

Sound effect:

```python
@dataclass
class SoundEffectNode:
    id: str
    order: int
    source: str
```

---

# Stable IDs

Where practical, create stable dialogue IDs that survive small unrelated edits.

This helps preserve:

- selected takes
- locked takes
- cached generations

Do not rely only on raw list index if a better stable matching strategy is available.

---

# Example complete script

```md
# The AI Show

## Introduction

Host: Welcome back to the show. Today we're talking about AI agents.

Co-Host: I've been looking forward to this one.

[PAUSE: 300ms]

Host [curious]: So what actually makes something an agent?

Guest: The simplest answer is that it can work toward a goal instead of only answering one prompt at a time.

Co-Host: That's where things start getting interesting.
```

Detected characters:

```txt
Host
Co-Host
Guest
```

Headings remain structure and are not spoken.

The explicit pause becomes a timeline node.

The `curious` tag becomes delivery metadata and is not spoken.
