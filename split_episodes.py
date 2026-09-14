"""Utility to split long podcast markdown scripts into clean, individual episode files."""

import sys
import re
from pathlib import Path

# Ensure utf-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def split_podcast_script(input_file: str = "podcast.md"):
    in_path = Path(input_file)
    if not in_path.exists():
        print(f"Error: {input_file} not found.")
        return

    text = in_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Find Part / Episode headings (# ... Part X)
    part_indices = []
    for idx, line in enumerate(lines):
        if line.strip().startswith("# ") and ("part" in line.lower() or "episode" in line.lower()):
            part_indices.append((idx, line.strip()))

    episodes = []
    if len(part_indices) > 1:
        for i in range(len(part_indices)):
            start_idx = part_indices[i][0]
            end_idx = part_indices[i+1][0] if i + 1 < len(part_indices) else len(lines)
            ep_lines = lines[start_idx:end_idx]
            episodes.append(("\n".join(ep_lines).strip(), part_indices[i][1]))
    else:
        # Split evenly into 5 parts (~2,150 turns each)
        chunk_size = max(1, len(lines) // 5)
        for i in range(5):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < 4 else len(lines)
            ep_lines = lines[start:end]
            title = f"# AI vs Human — Episode {i+1}"
            episodes.append((title + "\n\n" + "\n".join(ep_lines).strip(), title))

    print(f"🎙 Splitting {input_file} into {len(episodes)} episodic files:\n")
    for idx, (ep_content, ep_title) in enumerate(episodes, start=1):
        out_filename = f"episode_{idx}.md"
        out_path = Path(out_filename)
        out_path.write_text(ep_content, encoding="utf-8")
        
        words = len(ep_content.split())
        est_min = round(words / 140, 1)
        print(f"  ✅ {out_filename:15s} -> {words:,} words (~{est_min} mins) [{ep_title}]")

    print("\n✨ You can now generate any episode directly:")
    print("  python generate_podcast.py episode_1.md episode_1.wav")


if __name__ == "__main__":
    split_podcast_script("podcast.md")
