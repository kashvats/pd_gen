"""Normalize input formats before concatenation; never drop speech or disguise WAV as MP3."""
import json
import subprocess
import tempfile
import threading
import wave
from pathlib import Path
from typing import List, Tuple
from app.config.settings import Settings
from app.system.limits import get_system_limits


class FFmpegAudioEngine:
    _lock = threading.Lock()

    @staticmethod
    def get_duration_ms(file_path: str) -> int:
        path = Path(file_path)
        if not path.is_file():
            return 0
        try:
            with wave.open(str(path), "rb") as wf:
                return round(wf.getnframes() * 1000 / wf.getframerate())
        except (wave.Error, EOFError):
            pass
        probe = Settings.find_ffprobe()
        if not probe:
            return 0
        try:
            proc = subprocess.run([probe, "-v", "error", "-show_format", "-of", "json", str(path)],
                                  capture_output=True, text=True, timeout=15)
            if proc.returncode == 0:
                return round(float(json.loads(proc.stdout)["format"]["duration"]) * 1000)
        except (ValueError, KeyError, subprocess.SubprocessError):
            pass
        return 0

    @staticmethod
    def generate_silence_wav(output_path: Path, duration_ms: int, sample_rate: int = 44100) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            remaining = max(0, round(duration_ms * sample_rate / 1000))
            while remaining:
                count = min(remaining, sample_rate)
                wf.writeframes(b"\0\0" * count)
                remaining -= count
        return output_path

    @classmethod
    def assemble_timeline(cls, audio_segments: List[Tuple[str, int]], output_path: Path,
                          crossfade_ms=15, normalize=True, target_lufs=-16.0, output_format="mp3"):
        if not audio_segments:
            return False
        output_path = Path(output_path)
        fmt = output_format.lower().lstrip(".")
        codecs = {"mp3": ["-c:a", "libmp3lame", "-b:a", "192k"], "wav": ["-c:a", "pcm_s16le"],
                  "flac": ["-c:a", "flac"], "m4a": ["-c:a", "aac", "-b:a", "192k"]}
        if fmt not in codecs or output_path.suffix.lower() != f".{fmt}":
            raise ValueError("Output extension must match the requested audio format.")
        if any(not Path(path).is_file() for path, _ in audio_segments):
            raise RuntimeError("A dialogue take is missing. Regenerate it before exporting.")
        ffmpeg = Settings.find_ffmpeg()
        if not ffmpeg:
            raise RuntimeError("Install FFmpeg and ffprobe, or set FFMPEG_PATH / FFPROBE_PATH. No audio was exported.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        threads = str(get_system_limits().cpu_thread_budget)

        def run(args):
            result = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-nostdin",
                                     "-threads", threads, "-filter_threads", "1", *args],
                                    capture_output=True, text=True, timeout=3600)
            if result.returncode:
                raise RuntimeError(f"FFmpeg could not process audio: {result.stderr[-1500:]}")

        with cls._lock, tempfile.TemporaryDirectory(prefix="assembly_", dir=output_path.parent) as temp:
            temp = Path(temp)
            parts = []
            for index, (source, pause) in enumerate(audio_segments):
                part = temp / f"turn_{index}.wav"
                # Decode each source first. Concat demuxer cannot safely mix MP3 and WAV.
                duration = cls.get_duration_ms(source) / 1000
                if duration <= 0:
                    raise RuntimeError(f"Invalid audio take: {source}")
                fade = min(max(crossfade_ms, 0), 5) / 1000
                filters = ["aresample=44100"]
                if fade:
                    filters += [f"afade=t=in:d={fade}", f"afade=t=out:st={max(0, duration-fade)}:d={fade}"]
                run(["-i", str(Path(source).resolve()), "-vn", "-af", ",".join(filters),
                     "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(part)])
                parts.append(part.name)
                if pause > 0:
                    silence = temp / f"pause_{index}.wav"
                    cls.generate_silence_wav(silence, pause)
                    parts.append(silence.name)
            listing = temp / "concat.txt"
            # Relative generated names avoid quoting failures in user paths containing apostrophes.
            listing.write_text("".join(f"file '{name}'\n" for name in parts), encoding="utf-8")
            target = temp / f"final.{fmt}"
            args = ["-f", "concat", "-safe", "1", "-i", str(listing)]
            if normalize:
                args += ["-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11"]
            args += ["-ar", "44100", "-ac", "1", *codecs[fmt], str(target)]
            run(args)
            if cls.get_duration_ms(str(target)) <= 0:
                raise RuntimeError("Final audio validation failed; existing export was preserved.")
            target.replace(output_path)
        return True
