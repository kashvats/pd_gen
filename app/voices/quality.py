"""Audio quality diagnostics for voice cloning reference recordings."""

import io
import math
import struct
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import numpy as np


@dataclass
class AudioQualityReport:
    """Diagnostic report on voice reference recording quality."""
    file_path: str
    duration_sec: float = 0.0
    sample_rate: int = 44100
    channels: int = 1
    rms_db: float = -20.0
    peak_db: float = -3.0
    silence_percentage: float = 0.0
    is_clipping: bool = False
    is_too_quiet: bool = False
    is_too_short: bool = False
    score: int = 100  # 0 to 100
    status: str = "Excellent"  # Excellent, Good, Fair, Poor
    warnings: List[str] = field(default_factory=list)
    guidance: List[str] = field(default_factory=list)


def analyze_reference_audio(file_path: str) -> AudioQualityReport:
    """Analyzes a reference audio file and returns an AudioQualityReport."""
    path = Path(file_path)
    report = AudioQualityReport(file_path=file_path)

    if not path.exists():
        report.warnings.append(f"File not found: {file_path}")
        report.score = 0
        report.status = "Poor"
        return report

    # Load audio data (prefer standard wave or numpy)
    samples = None
    sample_rate = 44100
    channels = 1

    try:
        # Try reading standard WAV directly
        with wave.open(str(path), "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sampwidth = wf.getsampwidth()
            n_frames = wf.getnframes()
            duration = n_frames / sample_rate
            raw_bytes = wf.readframes(n_frames)

            if sampwidth == 2:  # 16-bit
                data = np.frombuffer(raw_bytes, dtype=np.int16)
                if channels > 1:
                    data = data[::channels]  # Take first channel
                samples = data.astype(np.float32) / 32768.0
            elif sampwidth == 3:  # 24-bit
                # 24-bit PCM conversion
                raw_ints = []
                for i in range(0, len(raw_bytes), 3 * channels):
                    b = raw_bytes[i:i+3]
                    val = int.from_bytes(b, byteorder='little', signed=True)
                    raw_ints.append(val)
                data = np.array(raw_ints, dtype=np.float32)
                samples = data / 8388608.0
            elif sampwidth == 4:  # 32-bit float or int
                data = np.frombuffer(raw_bytes, dtype=np.int32)
                if channels > 1:
                    data = data[::channels]
                samples = data.astype(np.float32) / 2147483648.0
    except Exception:
        # Fallback if non-wav or custom format
        pass

    if samples is None or len(samples) == 0:
        # If we couldn't parse wav directly, file might be mp3 or other format
        file_size = path.stat().st_size
        approx_sec = file_size / (44100 * 2)
        report.duration_sec = approx_sec
        report.warnings.append("Format could not be deeply analyzed, but file is accepted.")
        report.status = "Good"
        report.score = 80
        return report

    duration = len(samples) / sample_rate
    report.duration_sec = round(duration, 2)
    report.sample_rate = sample_rate
    report.channels = channels

    # Calculate Peak and RMS volume
    peak = float(np.max(np.abs(samples))) if len(samples) > 0 else 0.0
    rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) > 0 else 0.0

    peak_db = 20 * math.log10(max(1e-6, peak))
    rms_db = 20 * math.log10(max(1e-6, rms))

    report.peak_db = round(peak_db, 1)
    report.rms_db = round(rms_db, 1)

    # Detect clipping
    clipped_samples = np.sum(np.abs(samples) >= 0.999)
    if clipped_samples > 10 or peak_db >= -0.05:
        report.is_clipping = True
        report.warnings.append("Audio clipping detected: volume peaks are exceeding digital limit.")
        report.guidance.append("Lower your microphone gain or avoid shouting directly into mic.")
        report.score -= 25

    # Detect low volume
    if rms_db < -32.0:
        report.is_too_quiet = True
        report.warnings.append("Audio is very quiet (RMS below -32 dB).")
        report.guidance.append("Move closer to the microphone or increase input gain.")
        report.score -= 20

    # Detect excessive silence
    frame_len = int(sample_rate * 0.05)  # 50ms frames
    if len(samples) > frame_len:
        frames = samples[: len(samples) - (len(samples) % frame_len)].reshape(-1, frame_len)
        frame_rms = np.sqrt(np.mean(frames ** 2, axis=1))
        silence_threshold = max(1e-4, rms * 0.05)
        silent_frames = np.sum(frame_rms < silence_threshold)
        silence_pct = (silent_frames / len(frame_rms)) * 100.0
        report.silence_percentage = round(silence_pct, 1)
        if silence_pct > 40.0:
            report.warnings.append(f"High proportion of silence ({silence_pct:.0f}%).")
            report.guidance.append("Trim long silent pauses for cleaner voice training.")
            report.score -= 15

    # Duration checks
    if duration < 10.0:
        report.is_too_short = True
        report.warnings.append(f"Recording is short ({duration:.1f}s). Recommend at least 30-60s.")
        report.guidance.append("Record 1-3 minutes of continuous speech for higher voice accuracy.")
        report.score -= 20
    elif duration > 600.0:
        report.warnings.append("Sample is over 10 minutes; consider using a concise 2-3 minute highlight.")

    report.score = max(10, min(100, report.score))
    if report.score >= 85:
        report.status = "Excellent"
    elif report.score >= 70:
        report.status = "Good"
    elif report.score >= 50:
        report.status = "Fair"
    else:
        report.status = "Poor"

    return report
