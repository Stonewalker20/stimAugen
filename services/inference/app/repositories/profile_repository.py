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


def _is_seed_profile_id(profile_id: str) -> bool:
    return profile_id.startswith("sample_") or profile_id.startswith("sample-")


class ProfileRepository:
    def __init__(self, storage: StorageService) -> None:
        self.storage = storage
        self._ensure_seed_profiles()

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

    def _persist_artifact_path(self, base_dir: Path, artifact: dict[str, object]) -> dict[str, object]:
        persisted = dict(artifact)
        raw_path = Path(str(persisted.get("path", "")))
        if raw_path.is_absolute():
            try:
                persisted["path"] = str(raw_path.relative_to(base_dir))
            except ValueError:
                persisted["path"] = str(raw_path)
        else:
            persisted["path"] = str(raw_path)
        return persisted

    def _resolve_reference_path(self, base_dir: Path, raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute() and path.exists():
            return path
        candidate = base_dir / path if not path.is_absolute() else base_dir / "references" / path.name
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if not candidate.exists():
            _generate_seed_clip(candidate)
        return candidate

    def _ensure_seed_profiles(self) -> None:
        seeds = [
            {
                "id": "sample_warm_narrator",
                "name": "Warm Narrator",
                "description": "Steady everyday voice for reminders, timers, and home notices.",
                "clip_name": "warm-narrator.wav",
                "label": "Warm Narrator Sample",
                "defaultSettings": {
                    "speed": 1.0,
                    "strength": 0.55,
                    "pitchPreserve": True,
                    "cleanupLevel": 0.5,
                },
                "analysis": {
                    "estimatedPitchHz": 220.0,
                    "averageLevelDb": -18.0,
                    "notes": "Balanced and friendly. Good default for general home speech.",
                },
            },
            {
                "id": "sample-soft-announce",
                "name": "Soft Announcer",
                "description": "Gentler voice for bedtime, calm prompts, and ambient playback.",
                "clip_name": "soft-announce.wav",
                "label": "Soft Announcer Sample",
                "defaultSettings": {
                    "speed": 0.92,
                    "strength": 0.48,
                    "pitchPreserve": True,
                    "cleanupLevel": 0.42,
                },
                "analysis": {
                    "estimatedPitchHz": 198.0,
                    "averageLevelDb": -19.0,
                    "notes": "Softer and slower. Good for low-pressure prompts and story mode.",
                },
            },
        ]

        now = utc_now_iso()
        for seed in seeds:
            profile_id = str(seed["id"])
            manifest_path = self.storage.profile_manifest(profile_id)
            if manifest_path.exists():
                continue

            clip_path = self.storage.profile_dir(profile_id) / "references" / str(seed["clip_name"])
            if not clip_path.exists():
                _generate_seed_clip(clip_path)

            profile = {
                "id": profile_id,
                "name": seed["name"],
                "description": seed["description"],
                "consentConfirmed": True,
                "createdAt": now,
                "updatedAt": now,
                "embeddingStatus": "ready",
                "referenceClips": [
                    self._persist_artifact_path(
                        clip_path.parent.parent,
                        self._artifact_from_path(clip_path, label=str(seed["label"])),
                    ),
                ],
                "defaultSettings": seed["defaultSettings"],
                "analysis": seed["analysis"],
            }
            self.storage.write_json(manifest_path, profile)

    def _hydrate_profile(self, profile_id: str, payload: dict[str, object]) -> dict[str, object]:
        base_dir = self.storage.profile_dir(profile_id)
        clips: list[dict[str, object]] = []
        persisted_clips: list[dict[str, object]] = []
        changed = False
        for clip in payload.get("referenceClips", []):
            if not isinstance(clip, dict):
                continue
            raw_path = str(clip.get("path", ""))
            resolved = self._resolve_reference_path(base_dir, raw_path)
            clip_payload = self._artifact_from_path(resolved, label=str(clip.get("label", resolved.stem)))
            clips.append(clip_payload)
            persisted_clip = self._persist_artifact_path(base_dir, clip_payload)
            persisted_clips.append(persisted_clip)
            if Path(raw_path).is_absolute() or persisted_clip.get("path") != raw_path:
                changed = True
        hydrated = dict(payload)
        hydrated["referenceClips"] = clips
        if changed:
            hydrated["referenceClips"] = persisted_clips
            self.storage.write_json(self.storage.profile_manifest(profile_id), hydrated)
        return hydrated

    def list_profiles(self) -> list[dict[str, object]]:
        profiles: list[dict[str, object]] = []
        for manifest in sorted(self.storage.paths.profiles.glob("*/profile.json")):
            payload = self.storage.read_json(manifest, {})
            if isinstance(payload, dict):
                profiles.append(self._hydrate_profile(str(payload.get("id", manifest.parent.name)), payload))
        profiles.sort(key=lambda item: str(item.get("updatedAt", "")), reverse=True)
        profiles.sort(key=lambda item: 0 if _is_seed_profile_id(str(item.get("id", ""))) else 1)
        return profiles

    def get_profile(self, profile_id: str) -> dict[str, object] | None:
        payload = self.storage.read_json(self.storage.profile_manifest(profile_id), None)
        if isinstance(payload, dict):
            return self._hydrate_profile(profile_id, payload)
        return None

    def create_profile(self, payload: dict[str, object]) -> dict[str, object]:
        profile_id = make_id("profile")
        now = utc_now_iso()
        base_dir = self.storage.profile_dir(profile_id)
        reference_clips: list[dict[str, object]] = []
        for source in payload.get("referenceClipPaths", []):
            destination = self.storage.copy_reference_clip(profile_id, str(source))
            artifact = self._artifact_from_path(destination, label=destination.stem.replace("-", " ").title())
            reference_clips.append(self._persist_artifact_path(base_dir, artifact))
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
        return self._hydrate_profile(profile_id, profile)

    def update_profile(self, profile_id: str, patch: dict[str, object]) -> dict[str, object] | None:
        current = self.get_profile(profile_id)
        if current is None:
            return None
        current.update({key: value for key, value in patch.items() if value is not None})
        current["updatedAt"] = utc_now_iso()
        self.storage.write_json(self.storage.profile_manifest(profile_id), current)
        return current
