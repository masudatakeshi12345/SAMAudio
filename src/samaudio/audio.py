from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio
from pydub import AudioSegment


TARGET_SAMPLE_RATE = 16000


def load_audio(path: str | Path, sample_rate: int = TARGET_SAMPLE_RATE) -> tuple[torch.Tensor, int]:
    waveform, original_rate = torchaudio.load(str(path))
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    if original_rate != sample_rate:
        waveform = torchaudio.functional.resample(waveform, original_rate, sample_rate)
        original_rate = sample_rate
    return waveform, original_rate


def clip_audio(
    source_path: str | Path,
    start_seconds: float,
    end_seconds: float,
    destination_path: str | Path,
) -> Path:
    audio = AudioSegment.from_file(source_path)
    clipped = audio[int(start_seconds * 1000) : int(end_seconds * 1000)]
    destination = Path(destination_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    clipped.export(destination, format="wav")
    return destination


def save_waveform(destination: str | Path, waveform: torch.Tensor, sample_rate: int) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, np.squeeze(waveform.numpy()), sample_rate)
    return path
