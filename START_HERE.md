# Natural Speech Studio — updated project

Generate speech from **your supplied script**, with distinct neural voices for
conversation, podcasts, narration, or teaching. No LLM, auto-writing, invented
replies, added laughter, or fake breaths are part of generation.

## Hear the update first

Open `preview_natural.wav`. It was generated with the real Kokoro model from the
first four dialogue turns of your supplied `podcast.md`. `preview_script.md`
contains exactly those turns. It is a short voice-quality sample, not the full
podcast. Your original `podcast_master.wav` is preserved and is not the new sample.

## Setup

Use Python 3.10–3.12 (tested here with 3.12). Open a terminal in this folder.
A virtual environment is recommended:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/install_kokoro.py --download
```

On Linux/macOS, activate with `source .venv/bin/activate` instead.
The model installer explicitly downloads roughly 340 MB of free model files.
Models are **not bundled in this ZIP**. After installation, Kokoro runs offline.
It uses CPU inference with a bounded thread budget; the 4 GB GPU is not required.

FFmpeg and ffprobe must also be installed and available in PATH. Check:

```text
ffmpeg -version
ffprobe -version
```

Alternatively set `FFMPEG_PATH` and `FFPROBE_PATH` to the full executable paths.
Both WAV and compressed exports use FFmpeg. A missing encoder causes a clear
error instead of a fake MP3 or an incomplete file.

## Desktop app

```text
python main.py
```

1. Choose **File → Open Script** or paste into **Raw Markdown Source**.
2. Choose a Kokoro voice for each character in the cast panel.
3. Use **Test Voice** for a short voice preview. **New Take** generates a turn
   from your actual script; preview the resulting take in its card.
4. Adjust pace conservatively, usually 0.95–1.05. Teaching is a slower preset.
5. Choose WAV or MP3 and click **Generate Master Audio**.
6. Use **Folder** to locate `audio/final.wav` or `audio/final.mp3`.

New projects use Kokoro. Existing projects retain their saved assignments;
select neural voices if they reference old paid/system/cloning engines.
Completed takes and project settings are saved. Locked takes remain locked
across unrelated script edits. Unlock any old poor-quality take before replacing it.

The default cast is English. Kokoro voices in this build are American/British
English; do not assume natural Hindi or Hinglish pronunciation.

## Command line

```text
python generate_podcast.py my_script.md output.wav
python generate_podcast.py my_script.md output.mp3 --mode podcast
python generate_podcast.py lesson.md lesson.wav --mode teaching
python generate_podcast.py my_script.md output.wav --voice "Alex=am_michael" --voice "Maya=af_heart"
```

Available Kokoro IDs: `af_heart`, `am_michael`, `af_bella`, `am_fenrir`,
`bf_emma`, `bm_george`, `af_nicole`, `am_puck`.
The output extension determines the actual codec. The command exits unsuccessfully
when any turn fails and preserves completed work in the project directory.

## Script format

```markdown
# A conversation
Alex: Did you really build the whole thing yourself?
Maya: Yeah. It took most of the weekend, though.
Alex: That's pretty impressive.

[PAUSE: 500ms]

Maya: There are still a few things I want to improve.
```

For a lesson or plain narration, use `Teacher: your text` or `Narrator: your text`.
Continuation lines belong to the same turn. Headings are not spoken. Markdown
formatting is removed, links retain their visible words, and explicit pauses are
honored. Pronunciation dictionaries can intentionally change spoken spellings;
inspect them in Studio Tools. SFX directives are rejected in this speech-only
workflow instead of being silently dropped.

## Optional online voices

Edge voices send text to Microsoft's online TTS service. No API key or billing
integration is used. Availability is controlled by the upstream service.
Enable the explicit checkbox in the desktop app or use:

```text
python generate_podcast.py my_script.md output.mp3 --engine edge_tts --allow-online
```

Online failures stop with an error. They never switch voice, generate silence,
or fall back to paid services. Choose Kokoro explicitly for offline generation.

## Honest capability limits

These are neural **synthetic** voices. Naturalness varies with voice, punctuation,
pronunciation, language and recording context; indistinguishability from a real
human conversation is not guaranteed. Listen to the supplied preview first.
Neither Kokoro nor this Edge adapter follows arbitrary emotion/acting prompts;
unsupported sliders are disabled. Presets mainly adjust pace. Repeating a take
with unchanged Kokoro settings can produce the same audio; changing voice/pace
may be needed to improve it.

The uploaded “local cloning” adapter generated sine-wave tones, not speech.
It is disabled rather than presented as functional cloning. Reference recordings
and profile formats are preserved; this release does not provide real cloning.

## Validation

See `VALIDATION.md` for automated checks and real-model generation evidence.
Run regression tests with `python -m pytest -q`.
