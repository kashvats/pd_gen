"""Generate only the supplied script. No script writer, invented dialogue, or paid fallback."""
import argparse
from pathlib import Path
import shutil
import sys
from app.projects.manager import ProjectManager
from app.audio.generator import AudioGenerationEngine
from app.audio.assembler import TimelineAssembler
from app.tts.registry import tts_registry


def generate_podcast_from_md(md_file_path="podcast.md", output_audio_path="podcast_master.wav",
                             engine="kokoro", allow_online=False, mode="conversation", voice_map=None):
    source, output = Path(md_file_path), Path(output_audio_path).resolve()
    if output == source.resolve():
        raise ValueError("Choose a separate audio output path; the script must not be overwritten.")
    fmt = output.suffix.lower().lstrip(".")
    if fmt not in ("wav", "mp3", "flac", "m4a"):
        raise ValueError("Output must end in .wav, .mp3, .flac, or .m4a")
    script = source.read_text(encoding="utf-8-sig")
    if not script.strip():
        raise ValueError("Script is empty.")
    manager = ProjectManager()
    project = manager.create_project(source.stem, script)
    if not project.script_nodes or not project.speakers:
        raise ValueError("No dialogue found. Use 'Narrator: your text' or 'Speaker: dialogue'.")
    provider = tts_registry.get(engine)
    if provider is None or provider.category == "DISABLED":
        raise ValueError(f"Unavailable engine: {engine}")
    if not provider.capabilities.local and not allow_online:
        raise ValueError("Edge sends your script to Microsoft. Pass --allow-online to enable it.")
    palette = provider.list_voices()
    voice_map = voice_map or {}
    unknown = set(voice_map) - set(project.speakers)
    if unknown:
        raise ValueError(f"Voice map contains unknown speakers: {sorted(unknown)}")
    used = set()
    for index, (name, profile) in enumerate(project.speakers.items()):
        available = {v.id: v for v in palette}
        selected = voice_map.get(name)
        if not selected:
            selected = (profile.voice_id if profile.provider == engine and profile.voice_id in available
                        and profile.voice_id not in used else next((v.id for v in palette if v.id not in used),
                                                                  palette[index % len(palette)].id))
        if selected not in available:
            raise ValueError(f"Unknown voice {selected}. Choices: {', '.join(available)}")
        used.add(selected)
        profile.provider, profile.voice_id, profile.voice_name = engine, selected, available[selected].name
        profile.delivery.pace = 0.95 if mode == "teaching" else 1.0
        profile.preset = {"teaching": "Narration", "podcast": "Podcast", "conversation": "Natural Conversation"}[mode]
        print(f"{name}: {profile.voice_name}")
    project.settings.output_format = fmt
    project.settings.allow_online = allow_online
    project.settings.default_pause_ms = {"conversation": 280, "podcast": 320, "teaching": 420}[mode]
    directory = manager.get_project_dir(project.id)
    manager.save_project(project)
    try:
        ok = AudioGenerationEngine().generate_project(project, directory,
             progress_callback=lambda message, progress: print(f"{progress:.0%} {message}", flush=True))
        if not ok:
            errors = [g.error_message for g in project.segments_generation.values() if g.status == "failed"]
            raise RuntimeError("; ".join(errors) or "No speech generated.")
        manifest = TimelineAssembler.assemble(project, directory)
        if not manifest:
            raise RuntimeError("No complete timeline was produced.")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest.final_audio_path, output)
        print(f"Saved {output}")
        return True
    finally:
        manager.save_project(project)  # Preserve completed takes even on failure.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", nargs="?", default="podcast.md")
    parser.add_argument("output", nargs="?", default="podcast_master.wav")
    parser.add_argument("--engine", choices=["kokoro", "edge_tts"], default="kokoro")
    parser.add_argument("--allow-online", action="store_true", help="Allow sending script text to Microsoft Edge TTS")
    parser.add_argument("--mode", choices=["conversation", "podcast", "teaching"], default="conversation")
    parser.add_argument("--voice", action="append", default=[], metavar="SPEAKER=VOICE_ID")
    args = parser.parse_args()
    try:
        mapping = dict(item.split("=", 1) for item in args.voice)
        generate_podcast_from_md(args.script, args.output, args.engine, args.allow_online, args.mode, mapping)
    except Exception as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
