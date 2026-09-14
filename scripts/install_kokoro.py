"""Explicit one-time model installation; synthesis never downloads weights."""
import argparse
from pathlib import Path
import shutil
import sys
import urllib.request
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "models" / "kokoro"
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = {"kokoro-v1.0.onnx": 250_000_000, "voices-v1.0.bin": 1_000_000}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download ~340 MB of free model/voice files")
    args = parser.parse_args()
    print("Kokoro 82M • Apache-2.0 model • MIT adapter\n"
          "Download: approximately 340 MB. CPU inference, no GPU required.\n"
          "RAM planning allowance: 2–4 GB (measure on your machine). No account or paid API.\n"
          f"Destination: {DEST}\nSource: {BASE}\n"
          "Model license: https://huggingface.co/hexgrad/Kokoro-82M\n", flush=True)
    if not args.download:
        print("Run again with --download to install, or place the two files here manually.")
        return 0
    DEST.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(DEST).free < 11 * 1024 ** 3:
        raise RuntimeError("Leave at least 11 GB free before model installation.")
    hashes = {}
    for name, minimum in FILES.items():
        target = DEST / name
        if not target.is_file() or target.stat().st_size < minimum:
            partial = target.with_suffix(target.suffix + ".part")
            try:
                print(f"Downloading {name}...", flush=True)
                with urllib.request.urlopen(BASE + name, timeout=60) as response, partial.open("wb") as out:
                    shutil.copyfileobj(response, out, length=1024 * 1024)
                if partial.stat().st_size < minimum:
                    raise RuntimeError(f"Incomplete or invalid download for {name}.")
                partial.replace(target)
            finally:
                partial.unlink(missing_ok=True)
        with target.open("rb") as f:
            hashes[name] = hashlib.file_digest(f, "sha256").hexdigest()
        print(f"Ready: {name}", flush=True)
    (DEST / "installed.json").write_text(json.dumps({"source": BASE, "sha256": hashes,
        "note": "Local fingerprints, not independently authenticated release checksums."}, indent=2))
    print("Installed. Start the app or run python generate_podcast.py your_script.md output.wav")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Installation failed: {exc}", file=sys.stderr)
        sys.exit(1)
