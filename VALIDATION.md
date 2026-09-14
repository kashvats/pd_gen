# Validation of the natural speech update

## Automated regression checks

`python -m pytest -q`: **37 passed**.

Checks cover complete-turn forwarding, real-adapter empty/silent-output rejection,
clear missing-model errors, disabled fake cloning, absence of mock/paid engines
from the production registry, permission before online requests, no silent voice
fallback, preservation of words/links/brackets, failure propagation, blocked
partial exports, leading pauses, no doubled explicit pause, stable unchanged turn
IDs, cached takes, distinct dynamic voices, mixed MP3/WAV/sample-rate assembly,
and failure instead of a falsely named MP3 when FFmpeg is missing.

Mock tones are used explicitly in plumbing tests only. These tests do not prove
that a voice sounds natural or that its pronunciation is correct.

## Real-model execution

Installed `kokoro-onnx==0.6.1`, the actual Kokoro v1.0 ONNX weights and voices
from the upstream model-files-v1.0 release. Ran:

```text
python generate_podcast.py preview_script.md preview_natural.wav
```

The input contains the first four dialogue turns from the uploaded `podcast.md`.
The real neural engine generated all four turns and the final WAV successfully.
Three voices were assigned: Michael, Heart and Bella. The resulting sample is
8.818 seconds, mono, 44,100 Hz PCM. No simulated provider was used for this sample.

Listen to `preview_natural.wav` to evaluate the sound. The execution environment
has no working audio playback device, so subjective listening quality and
word-for-word speech recognition were not verified here. This is not a claim
that synthetic speech is indistinguishable from live conversation.

## Desktop smoke check

Constructed the PySide6 application with its actual theme, loaded a two-speaker
script, checked distinct voice assignments and rendered/inspected the window in
Qt offscreen mode. Native audio playback and the user's Windows/GPU environment
were not tested. Generation was tested on CPU, not on the target laptop.

## Not included / not claimed

- Model weights in the ZIP (install explicitly using START_HERE.md).
- A complete new render of the long original podcast.
- Real voice cloning, unrestricted emotion prompting or automatic script writing.
- Live Edge service verification; its error/permission behavior was regression tested.
- Guaranteed realistic pronunciation for languages other than the supported English cast.

The original script and original master audio are preserved byte-for-byte.
