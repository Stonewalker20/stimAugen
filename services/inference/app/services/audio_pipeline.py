from __future__ import annotations

import aifc
import audioop
import json
import math
import shutil
import struct
import subprocess
import tempfile
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.api.errors import AppError
from app.models.common import AudioArtifact

TARGET_SAMPLE_RATE = 22050
TARGET_CHANNELS = 1
TARGET_WIDTH = 2

AudioPipelineError = AppError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class PreparedAudio:
    path: Path
    sample_rate: int
    channels: int
    duration_ms: int
    peak: int


@dataclass(slots=True)
class AudioBuffer:
    pcm_bytes: bytes
    sample_rate: int
    channels: int = 1
    sample_width: int = TARGET_WIDTH
    source_path: str | None = None
    format_name: str = "wav"
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def frame_count(self) -> int:
        return len(self.pcm_bytes) // max(1, self.sample_width * self.channels)

    @property
    def duration_seconds(self) -> float:
        if self.sample_rate <= 0:
            return 0.0
        return self.frame_count / float(self.sample_rate)

    @property
    def duration_ms(self) -> int:
        return int(round(self.duration_seconds * 1000))


@dataclass(slots=True)
class AudioWaveform:
    points: list[float]
    peak: float
    rms: float
    sample_rate: int
    duration_ms: int

    def to_json(self) -> str:
        return json.dumps(
            {
                "points": self.points,
                "peak": self.peak,
                "rms": self.rms,
                "sample_rate": self.sample_rate,
                "duration_ms": self.duration_ms,
            }
        )


class AudioPipeline:
    def __init__(self) -> None:
        self.ffmpeg_available = shutil.which("ffmpeg") is not None

    def capabilities(self) -> list[dict[str, object]]:
        return [
            {
                "id": "audio_pipeline",
                "label": "Audio pipeline",
                "available": True,
                "detail": "Built-in WAV processing with optional ffmpeg export.",
            },
            {
                "id": "ffmpeg",
                "label": "FFmpeg",
                "available": self.ffmpeg_available,
                "detail": "Used for MP3 export and non-WAV transcoding.",
            },
        ]

    def prepare_input(self, source_path: str | Path, work_dir: Path, stem: str = "prepared") -> PreparedAudio:
        source = Path(source_path).expanduser().resolve()
        if not source.exists():
            raise AppError(code="audio_not_found", message="Input audio file was not found.", details=str(source))

        wav_path = work_dir / f"{stem}.wav"
        if source.suffix.lower() == ".wav":
            shutil.copy2(source, wav_path)
        elif source.suffix.lower() in {".aif", ".aiff"}:
            self._convert_aiff_to_wav(source, wav_path)
        elif self.ffmpeg_available:
            self._ffmpeg_to_wav(source, wav_path)
        else:
            raise AppError(
                code="unsupported_audio_format",
                message="Only WAV input is supported without ffmpeg.",
                details=str(source),
            )

        frames, sample_rate, channels = self._read_wave(wav_path)
        mono = self._to_mono(frames, channels)
        resampled = self._resample(mono, sample_rate, TARGET_SAMPLE_RATE)
        trimmed = self._trim_silence(resampled)
        normalized = self._normalize_peak(trimmed)
        self._write_wave(wav_path, normalized, TARGET_SAMPLE_RATE, TARGET_CHANNELS)

        artifact = self.inspect_audio(wav_path, kind="input", label=source.stem)
        return PreparedAudio(
            path=wav_path,
            sample_rate=artifact.sample_rate,
            channels=artifact.channels,
            duration_ms=artifact.duration_ms,
            peak=self._peak(normalized),
        )

    def load(
        self,
        source: str | Path | AudioBuffer | bytes,
        *,
        target_sample_rate: int | None = None,
        force_mono: bool = True,
    ) -> AudioBuffer:
        if isinstance(source, AudioBuffer):
            buffer = source
        elif isinstance(source, bytes):
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(source)
                tmp_path = Path(tmp.name)
            try:
                buffer = self.load(tmp_path, target_sample_rate=target_sample_rate, force_mono=force_mono)
            finally:
                tmp_path.unlink(missing_ok=True)
            return buffer
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                prepared = self.prepare_input(source, Path(temp_dir))
                frames, _, _ = self._read_wave(prepared.path)
                buffer = AudioBuffer(
                    pcm_bytes=frames,
                    sample_rate=prepared.sample_rate,
                    channels=prepared.channels,
                    sample_width=TARGET_WIDTH,
                    source_path=str(prepared.path),
                )

        if force_mono:
            buffer = self.normalize_mono(buffer)
        if target_sample_rate and buffer.sample_rate != target_sample_rate:
            buffer = self.resample(buffer, target_sample_rate)
        return buffer

    def normalize_mono(self, buffer: AudioBuffer) -> AudioBuffer:
        if buffer.channels <= 1:
            return buffer
        return AudioBuffer(
            pcm_bytes=self._to_mono(buffer.pcm_bytes, buffer.channels),
            sample_rate=buffer.sample_rate,
            channels=1,
            sample_width=buffer.sample_width,
            source_path=buffer.source_path,
            format_name=buffer.format_name,
            metadata=dict(buffer.metadata),
        )

    def resample(self, buffer: AudioBuffer, target_sample_rate: int) -> AudioBuffer:
        if buffer.sample_rate == target_sample_rate:
            return buffer
        return AudioBuffer(
            pcm_bytes=self._resample(buffer.pcm_bytes, buffer.sample_rate, target_sample_rate),
            sample_rate=target_sample_rate,
            channels=buffer.channels,
            sample_width=buffer.sample_width,
            source_path=buffer.source_path,
            format_name=buffer.format_name,
            metadata=dict(buffer.metadata),
        )

    def trim_silence(self, buffer: AudioBuffer, threshold: int = 350) -> AudioBuffer:
        return AudioBuffer(
            pcm_bytes=self._trim_silence(buffer.pcm_bytes, threshold=threshold),
            sample_rate=buffer.sample_rate,
            channels=buffer.channels,
            sample_width=buffer.sample_width,
            source_path=buffer.source_path,
            format_name=buffer.format_name,
            metadata=dict(buffer.metadata),
        )

    def normalize_loudness(self, buffer: AudioBuffer, target_dbfs: float = -16.0) -> AudioBuffer:
        if not buffer.pcm_bytes:
            return buffer
        peak = self._peak(buffer.pcm_bytes)
        if peak == 0:
            return buffer
        target_peak = int(26000 * (10 ** ((target_dbfs + 16.0) / 20.0)))
        gain = min(4.0, max(0.1, target_peak / peak))
        return AudioBuffer(
            pcm_bytes=audioop.mul(buffer.pcm_bytes, buffer.sample_width, gain),
            sample_rate=buffer.sample_rate,
            channels=buffer.channels,
            sample_width=buffer.sample_width,
            source_path=buffer.source_path,
            format_name=buffer.format_name,
            metadata=dict(buffer.metadata),
        )

    def chunk(self, buffer: AudioBuffer, *, chunk_ms: int, overlap_ms: int = 0) -> list[AudioBuffer]:
        if chunk_ms <= 0:
            raise AudioPipelineError(code="invalid_chunk_size", message="chunk_ms must be greater than zero.")
        if overlap_ms < 0 or overlap_ms >= chunk_ms:
            raise AudioPipelineError(code="invalid_overlap", message="overlap_ms must be non-negative and smaller than chunk_ms.")
        frames_per_chunk = max(1, int(buffer.sample_rate * chunk_ms / 1000))
        frames_overlap = int(buffer.sample_rate * overlap_ms / 1000)
        step_frames = max(1, frames_per_chunk - frames_overlap)
        frame_size = buffer.channels * buffer.sample_width
        chunks: list[AudioBuffer] = []
        for start_frame in range(0, buffer.frame_count, step_frames):
            start_byte = start_frame * frame_size
            end_byte = start_byte + frames_per_chunk * frame_size
            pcm = buffer.pcm_bytes[start_byte:end_byte]
            if not pcm:
                break
            chunks.append(
                AudioBuffer(
                    pcm_bytes=pcm,
                    sample_rate=buffer.sample_rate,
                    channels=buffer.channels,
                    sample_width=buffer.sample_width,
                    source_path=buffer.source_path,
                    format_name=buffer.format_name,
                    metadata=dict(buffer.metadata),
                )
            )
        return chunks

    def generate_waveform_preview(self, buffer: AudioBuffer, *, bins: int = 120) -> AudioWaveform:
        if bins <= 0:
            raise AudioPipelineError(code="invalid_waveform_bins", message="bins must be positive.")
        if not buffer.pcm_bytes:
            return AudioWaveform(points=[0.0] * bins, peak=0.0, rms=0.0, sample_rate=buffer.sample_rate, duration_ms=0)
        frame_size = max(1, buffer.channels * buffer.sample_width)
        total_frames = max(1, buffer.frame_count)
        frames_per_bin = max(1, total_frames // bins)
        points: list[float] = []
        peak = 0.0
        rms_total = 0.0
        full_scale = float((1 << (buffer.sample_width * 8 - 1)) - 1)
        for index in range(bins):
            start = index * frames_per_bin * frame_size
            end = len(buffer.pcm_bytes) if index == bins - 1 else (index + 1) * frames_per_bin * frame_size
            chunk = buffer.pcm_bytes[start:end]
            if not chunk:
                points.append(0.0)
                continue
            chunk_peak = audioop.max(chunk, buffer.sample_width) / full_scale
            chunk_rms = audioop.rms(chunk, buffer.sample_width) / full_scale
            peak = max(peak, chunk_peak)
            rms_total += chunk_rms
            points.append(min(1.0, max(0.0, chunk_peak)))
        rms = rms_total / max(1, len(points))
        return AudioWaveform(points=points, peak=peak, rms=rms, sample_rate=buffer.sample_rate, duration_ms=buffer.duration_ms)

    def pipeline(
        self,
        source: str | Path | AudioBuffer | bytes,
        *,
        target_sample_rate: int | None = None,
        normalize: bool = True,
        trim: bool = True,
        loudness: bool = True,
    ) -> AudioBuffer:
        buffer = self.load(source, target_sample_rate=target_sample_rate, force_mono=True)
        if trim:
            buffer = self.trim_silence(buffer)
        if loudness:
            buffer = self.normalize_loudness(buffer)
        if normalize and buffer.sample_rate <= 0:
            raise AudioPipelineError(code="invalid_sample_rate", message="Audio sample rate must be positive.")
        return buffer

    def inspect_audio(self, path: str | Path, *, kind: str, label: str, job_id: str | None = None) -> AudioArtifact:
        audio_path = Path(path)
        if audio_path.suffix.lower() == ".wav":
            with wave.open(str(audio_path), "rb") as handle:
                frames = handle.getnframes()
                rate = handle.getframerate()
                channels = handle.getnchannels()
            duration_ms = int((frames / max(rate, 1)) * 1000)
            fmt = "wav"
        else:
            duration_ms = 0
            rate = TARGET_SAMPLE_RATE
            channels = 1
            fmt = audio_path.suffix.lower().lstrip(".")
        return AudioArtifact(
            id=audio_path.stem,
            jobId=job_id,
            kind=kind,
            label=label,
            path=str(audio_path),
            format=fmt,
            durationMs=duration_ms,
            sampleRate=rate,
            channels=channels,
            createdAt=utc_now(),
        )

    def generate_waveform(self, source_path: str | Path, destination_path: str | Path, points: int = 120) -> Path:
        frames, _, channels = self._read_wave(Path(source_path))
        mono = self._to_mono(frames, channels)
        samples = self._bytes_to_samples(mono)
        if not samples:
            buckets = [0] * points
        else:
            bucket_size = max(1, len(samples) // points)
            buckets = []
            for index in range(0, len(samples), bucket_size):
                chunk = samples[index : index + bucket_size]
                buckets.append(int(sum(abs(sample) for sample in chunk) / len(chunk)))
            buckets = (buckets + [0] * points)[:points]
        destination = Path(destination_path)
        destination.write_text(json.dumps({"points": buckets}), encoding="utf-8")
        return destination

    def export(
        self,
        source_path: str | Path | AudioBuffer,
        destination_path: str | Path,
        fmt: str | None = None,
        *,
        format: str | None = None,
    ) -> Path:
        fmt = (format or fmt or "wav").lower()
        destination = Path(destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "wav":
            if isinstance(source_path, AudioBuffer):
                self._write_wave(destination, source_path.pcm_bytes, source_path.sample_rate, source_path.channels)
            else:
                shutil.copy2(Path(source_path), destination)
            return destination
        if fmt == "mp3":
            if not self.ffmpeg_available:
                raise AppError(
                    code="ffmpeg_required",
                    message="MP3 export requires ffmpeg to be installed locally.",
                )
            temp_source: Path | None = None
            if isinstance(source_path, AudioBuffer):
                temp_source = destination.with_suffix(".wav")
                self._write_wave(temp_source, source_path.pcm_bytes, source_path.sample_rate, source_path.channels)
                source = temp_source
            else:
                source = Path(source_path)
            command = [
                "ffmpeg",
                "-y",
                "-i",
                str(source),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "4",
                str(destination),
            ]
            completed = subprocess.run(command, capture_output=True, text=True)
            if completed.returncode != 0:
                raise AppError(code="mp3_export_failed", message="MP3 export failed.", details=completed.stderr)
            if temp_source is not None:
                temp_source.unlink(missing_ok=True)
            return destination
        raise AppError(code="unsupported_export_format", message=f"Unsupported export format: {fmt}")

    def transform_samples(self, source_path: str | Path, destination_path: str | Path, transform: callable) -> Path:
        frames, rate, channels = self._read_wave(Path(source_path))
        mono = self._to_mono(frames, channels)
        samples = self._bytes_to_samples(mono)
        transformed = transform(samples, rate)
        self._write_wave(Path(destination_path), self._samples_to_bytes(transformed), rate, 1)
        return Path(destination_path)

    def synthesize_tone(self, destination_path: str | Path, duration_seconds: float, frequency: float = 220.0) -> Path:
        destination = Path(destination_path)
        total_samples = max(1, int(duration_seconds * TARGET_SAMPLE_RATE))
        samples = []
        for index in range(total_samples):
            value = int(math.sin((index / TARGET_SAMPLE_RATE) * math.tau * frequency) * 10000)
            samples.append(value)
        self._write_wave(destination, self._samples_to_bytes(samples), TARGET_SAMPLE_RATE, 1)
        return destination

    def estimate_profile_analysis(self, source_path: str | Path) -> dict[str, float]:
        frames, rate, channels = self._read_wave(Path(source_path))
        mono = self._to_mono(frames, channels)
        samples = self._bytes_to_samples(mono)
        if not samples:
            return {"estimatedPitchHz": 180.0, "averageLevelDb": -24.0}
        zero_crossings = 0
        for left, right in zip(samples, samples[1:]):
            if (left <= 0 < right) or (left >= 0 > right):
                zero_crossings += 1
        duration_seconds = max(len(samples) / rate, 0.001)
        estimated_pitch = max(80.0, min(320.0, (zero_crossings / 2) / duration_seconds))
        rms = max(audioop.rms(mono, TARGET_WIDTH), 1)
        average_level = 20 * math.log10(rms / 32767)
        return {"estimatedPitchHz": estimated_pitch, "averageLevelDb": average_level}

    def _ffmpeg_to_wav(self, source: Path, destination: Path) -> None:
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-ac",
            str(TARGET_CHANNELS),
            "-ar",
            str(TARGET_SAMPLE_RATE),
            str(destination),
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            raise AppError(code="ffmpeg_transcode_failed", message="Audio import failed.", details=completed.stderr)

    def _convert_aiff_to_wav(self, source: Path, destination: Path) -> None:
        with aifc.open(str(source), "rb") as handle:
            frames = handle.readframes(handle.getnframes())
            sample_rate = handle.getframerate()
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
        if sample_width != TARGET_WIDTH:
            frames = audioop.lin2lin(frames, sample_width, TARGET_WIDTH)
        if channels > 1:
            frames = audioop.tomono(frames, TARGET_WIDTH, 0.5, 0.5)
            channels = 1
        if sample_rate != TARGET_SAMPLE_RATE:
            frames, _ = audioop.ratecv(frames, TARGET_WIDTH, channels, sample_rate, TARGET_SAMPLE_RATE, None)
            sample_rate = TARGET_SAMPLE_RATE
        self._write_wave(destination, frames, sample_rate, channels)

    def _read_wave(self, path: Path) -> tuple[bytes, int, int]:
        with wave.open(str(path), "rb") as handle:
            sample_width = handle.getsampwidth()
            frames = handle.readframes(handle.getnframes())
            channels = handle.getnchannels()
            rate = handle.getframerate()
        if sample_width != TARGET_WIDTH:
            frames = audioop.lin2lin(frames, sample_width, TARGET_WIDTH)
        return frames, rate, channels

    def _write_wave(self, path: Path, frames: bytes, sample_rate: int, channels: int) -> None:
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(channels)
            handle.setsampwidth(TARGET_WIDTH)
            handle.setframerate(sample_rate)
            handle.writeframes(frames)

    def _to_mono(self, frames: bytes, channels: int) -> bytes:
        if channels <= 1:
            return frames
        return audioop.tomono(frames, TARGET_WIDTH, 0.5, 0.5)

    def _resample(self, frames: bytes, source_rate: int, target_rate: int) -> bytes:
        if source_rate == target_rate:
            return frames
        resampled, _ = audioop.ratecv(frames, TARGET_WIDTH, TARGET_CHANNELS, source_rate, target_rate, None)
        return resampled

    def _trim_silence(self, frames: bytes, threshold: int = 350) -> bytes:
        samples = self._bytes_to_samples(frames)
        if not samples:
            return frames
        start = 0
        end = len(samples)
        while start < len(samples) and abs(samples[start]) < threshold:
            start += 1
        while end > start and abs(samples[end - 1]) < threshold:
            end -= 1
        if start >= end:
            return frames
        return self._samples_to_bytes(samples[start:end])

    def _normalize_peak(self, frames: bytes, target_peak: int = 26000) -> bytes:
        peak = self._peak(frames)
        if peak == 0:
            return frames
        gain = min(4.0, target_peak / peak)
        return audioop.mul(frames, TARGET_WIDTH, gain)

    def _peak(self, frames: bytes) -> int:
        return audioop.max(frames, TARGET_WIDTH) if frames else 0

    def _bytes_to_samples(self, frames: bytes) -> list[int]:
        if not frames:
            return []
        count = len(frames) // TARGET_WIDTH
        return list(struct.unpack("<" + ("h" * count), frames))

    def _samples_to_bytes(self, samples: list[int]) -> bytes:
        clamped = [max(-32768, min(32767, int(sample))) for sample in samples]
        return struct.pack("<" + ("h" * len(clamped)), *clamped) if clamped else b""
