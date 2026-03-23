from __future__ import annotations

import math
import wave
from array import array
from pathlib import Path

from app.services.audio_pipeline import AudioPipeline


def _write_wav(path: Path, *, sample_rate: int = 16000, duration_s: float = 1.0, channels: int = 2) -> None:
    total_frames = int(sample_rate * duration_s)
    left = array("h")
    right = array("h")
    for index in range(total_frames):
        t = index / sample_rate
        tone = math.sin(2 * math.pi * 220 * t)
        silence = 0.0 if index < sample_rate // 10 or index > total_frames - sample_rate // 10 else 1.0
        left.append(int(12000 * tone * silence))
        right.append(int(9000 * math.sin(2 * math.pi * 330 * t) * silence))
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        interleaved = bytearray()
        for l, r in zip(left, right, strict=True):
            interleaved.extend(l.to_bytes(2, "little", signed=True))
            interleaved.extend(r.to_bytes(2, "little", signed=True))
        wav_file.writeframes(bytes(interleaved))


def test_audio_pipeline_load_trim_waveform_and_export(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    _write_wav(source)

    pipeline = AudioPipeline()
    load = getattr(pipeline, "load", None)

    if load is not None:
        buffer = load(source, target_sample_rate=24000, force_mono=True)

        assert buffer.sample_rate == 24000
        assert buffer.channels == 1
        assert buffer.duration_ms > 0

        trimmed = pipeline.trim_silence(buffer)
        normalized = pipeline.normalize_loudness(trimmed)
        chunks = pipeline.chunk(normalized, chunk_ms=250, overlap_ms=50)
        waveform = pipeline.generate_waveform_preview(normalized, bins=64)

        assert len(chunks) >= 1
        assert len(waveform.points) == 64
        assert 0.0 <= waveform.peak <= 1.0
        assert waveform.duration_ms == normalized.duration_ms

        wav_path = tmp_path / "export.wav"
        exported = pipeline.export(normalized, wav_path, format="wav")
        assert exported.exists()

        if pipeline.ffmpeg_available:
            mp3_path = tmp_path / "export.mp3"
            exported_mp3 = pipeline.export(normalized, mp3_path, format="mp3")
            assert exported_mp3.exists()
        return

    prepared = pipeline.prepare_input(source, tmp_path)
    assert prepared.path.exists()
    assert prepared.sample_rate > 0
    assert prepared.channels in (1, 2)

    artifact = pipeline.inspect_audio(source, kind="input", label="Source Audio")
    assert artifact.path == str(source)

    waveform_path = pipeline.generate_waveform(source, tmp_path / "waveform.json", points=64)
    assert waveform_path.exists()

    wav_path = tmp_path / "export.wav"
    exported = pipeline.export(source, wav_path, format="wav")
    assert exported.exists()

    if pipeline.ffmpeg_available:
        mp3_path = tmp_path / "export.mp3"
        exported_mp3 = pipeline.export(source, mp3_path, format="mp3")
        assert exported_mp3.exists()
