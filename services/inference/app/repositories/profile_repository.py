from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from app.services.storage import StorageService
from app.utils.clock import utc_now_iso
from app.utils.ids import make_id


def _probe_wav(path: Path) -> tuple[int, int, int]:
    try:
        with wave.open(str(path), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            duration_ms = int((wav_file.getnframes() / max(sample_rate, 1)) * 1000)
            return sample_rate, channels, duration_ms
    except wave.Error:
        return 0, 1, 0


def _generate_seed_clip(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 22050
    duration = 0.75
    amplitude = 9000
    samples: list[bytes] = []
    total_frames = int(sample_rate * duration)
    for index in range(total_frames):
        envelope = 0.3 + 0.7 * (index / total_frames)
        tone = math.sin(2 * math.pi * 220 * (index / sample_rate))
        value = int(amplitude * envelope * tone)
        samples.append(struct.pack("<h", value))
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"".join(samples))


class ProfileRepository:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage
        self._ensure_seed_profile()

    def _artifact_from_path(self, path: Path, *, label: str, kind: str = "reference") -> dict[str, object]:
        sample_rate, channels, duration_ms = _probe_wav(path)
        return {
            "id": make_id("artifact"),
            "jobId": None,
            "kind": kind,
            "label": label,
            "path": str(path),
            "format": path.suffix.lstrip(".").lower() or "wav",
            "durationMs": duration_ms,
            "sampleRate": sample_rate,
            "channels": channels,
            "createdAt": utc_now_iso(),
        }

    def _ensure_seed_profile(self) -> None:
        if self.storage.profile_manifest("sample_warm_narrator").exists():
            return
        profile_id = "sample_warm_narrator"
        clip_path = self.storage.profile_dir(profile_id) / "references" / "warm-narrator.wav"
        if not clip_path.exists():
            _generate_seed_clip(clip_path)
        now = utc_now_iso()
        seed = {
            "id": profile_id,
            "name": "Warm Narrator",
            "description": "Seed example profile for local testing.",
            "consentConfirmed": True,
            "createdAt": now,
            "updatedAt": now,
            "embeddingStatus": "ready",
            "referenceClips": [self._artifact_from_path(clip_path, label="Warm Narrator Sample")],
            "defaultSettings": {
                "speed": 1.0,
                "strength": 0.55,
                "pitchPreserve": True,
                "cleanupLevel": 0.5,
            },
            "analysis": {
                "estimatedPitchHz": 220.0,
                "averageLevelDb": -18.0,
                "notes": "Generated seed profile for MVP smoke testing.",
            },
        }
        self.storage.write_json(self.storage.profile_manifest(profile_id), seed)

    def _hydrate_profile(self, profile_id: str, payload: dict[str, object]) -> dict[str, object]:
        base_dir = self.storage.profile_dir(profile_id)
        clips: list[dict[str, object]] = []
        changed = False
        for clip in payload.get("referenceClips", []):
            if not isinstance(clip, dict):
                continue
            raw_path = Path(str(clip.get("path", "")))
            resolved = raw_path if raw_path.is_absolute() else (base_dir / raw_path)
            if not resolved.exists():
                resolved.parent.mkdir(parents=True, exist_ok=True)
                if resolved.suffix.lower() != ".wav":
                    resolved = resolved.with_suffix(".wav")
                if not resolved.exists():
                    _generate_seed_clip(resolved)
                changed = True
            clip_payload = self._artifact_from_path(resolved, label=str(clip.get("label", resolved.stem)))
            clips.append(clip_payload)
        hydrated = dict(payload)
        hydrated["referenceClips"] = clips
        if changed or any(not Path(str(clip.get("path", ""))).is_absolute() for clip in payload.get("referenceClips", [])):
            self.storage.write_json(self.storage.profile_manifest(profile_id), hydrated)
        return hydrated

    def list_profiles(self) -> list[dict[str, object]]:
        profiles: list[dict[str, object]] = []
        for manifest in sorted(self.storage.paths.profiles.glob("*/profile.json")):
            payload = self.storage.read_json(manifest, {})
            if isinstance(payload, dict):
                profiles.append(self._hydrate_profile(str(payload.get("id", manifest.parent.name)), payload))
        profiles.sort(key=lambda item: str(item.get("updatedAt", "")), reverse=True)
        return profiles

    def get_profile(self, profile_id: str) -> dict[str, object] | None:
        payload = self.storage.read_json(self.storage.profile_manifest(profile_id), None)
        if isinstance(payload, dict):
            return self._hydrate_profile(profile_id, payload)
        return None

    def create_profile(self, payload: dict[str, object]) -> dict[str, object]:
        profile_id = make_id("profile")
        now = utc_now_iso()
        reference_clips: list[dict[str, object]] = []
        for source in payload.get("referenceClipPaths", []):
            destination = self.storage.copy_reference_clip(profile_id, str(source))
            reference_clips.append(self._artifact_from_path(destination, label=destination.stem.replace("-", " ").title()))
        profile = {
            "id": profile_id,
            "name": payload["name"],
            "description": payload.get("description"),
            "consentConfirmed": bool(payload.get("consentConfirmed")),
            "createdAt": now,
            "updatedAt": now,
            "embeddingStatus": "ready",
            "referenceClips": reference_clips,
            "defaultSettings": {
                "speed": 1.0,
                "strength": 0.65,
                "pitchPreserve": True,
                "cleanupLevel": 0.5,
            },
            "analysis": None,
        }
        self.storage.write_json(self.storage.profile_manifest(profile_id), profile)
        return profile

    def update_profile(self, profile_id: str, patch: dict[str, object]) -> dict[str, object] | None:
        current = self.get_profile(profile_id)
        if current is None:
            return None
        current.update({key: value for key, value in patch.items() if value is not None})
        current["updatedAt"] = utc_now_iso()
        self.storage.write_json(self.storage.profile_manifest(profile_id), current)
        return current
