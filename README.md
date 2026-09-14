# Natural Speech Studio

A personal Python/PySide6 desktop application that converts supplied Markdown
scripts into multi-speaker neural speech. It also has a command-line generator.

**Start with [START_HERE.md](START_HERE.md).** It includes setup, usage, voice
selection, exact limitations, and how to listen to the generated sample.

- Real offline Kokoro neural voices on CPU after explicit model installation.
- Optional Edge online voices with explicit script-upload permission.
- Complete turns, stable cast assignments, pronunciation controls, conversational
  pauses, cached/locked takes, and proper WAV/MP3/FLAC/M4A encoding.
- No paid-provider registration, silent voice fallback, fake cloning or silence
  substituted for failed speech.
- Generation uses only your supplied script. The old `scripts/build_episodes.py`
  and `scripts/build_full_episodes.py` authoring examples are retained as original
  files, but are not called by the app or generator.

Your original script/audio are preserved. Model weights and test-generated
project data are excluded from this source ZIP.

The architecture/specification documents include longer-term goals. The
implementation status below and START_HERE describe what works in this release.
