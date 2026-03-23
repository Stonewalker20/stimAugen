from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.profile_service import ProfileService


def _accepted_job(kind: str, job_id: str) -> dict[str, Any]:
    return {
        "jobId": job_id,
        "kind": kind,
        "status": "queued",
        "progress": 0,
        "createdAt": "2026-03-23T00:00:00+00:00",
        "pollUrl": f"/jobs/{job_id}",
    }


def _artifact(path: str, *, kind: str = "output", label: str = "Result") -> dict[str, Any]:
    return {
        "id": "artifact_001",
        "jobId": None,
        "kind": kind,
        "label": label,
        "path": path,
        "format": "wav",
        "durationMs": 1200,
        "sampleRate": 24000,
        "channels": 1,
        "createdAt": "2026-03-23T00:00:00+00:00",
    }


@dataclass
class FakeProfileRepository:
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)

    def list_profiles(self) -> list[dict[str, Any]]:
        return list(self.profiles.values())

    def create_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        profile_id = f"profile_{len(self.profiles) + 1:03d}"
        profile = {
            "id": profile_id,
            "name": payload["name"],
            "description": payload.get("description"),
            "consentConfirmed": payload.get("consentConfirmed", False),
            "createdAt": "2026-03-23T00:00:00+00:00",
            "updatedAt": "2026-03-23T00:00:00+00:00",
            "embeddingStatus": "ready",
            "referenceClips": [
                _artifact(path, kind="reference", label=Path(path).stem.replace("-", " ").title())
                for path in payload.get("referenceClipPaths", [])
            ],
            "defaultSettings": {
                "speed": 1.0,
                "strength": 0.65,
                "pitchPreserve": True,
                "cleanupLevel": 0.5,
            },
            "analysis": None,
        }
        self.profiles[profile_id] = profile
        return profile

    def update_profile(self, profile_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        current = self.profiles.get(profile_id)
        if current is None:
            return None
        current.update({key: value for key, value in patch.items() if value is not None})
        current["updatedAt"] = "2026-03-23T00:00:00+00:00"
        return current

    def get_profile(self, profile_id: str) -> dict[str, Any] | None:
        return self.profiles.get(profile_id)


@dataclass
class FakeSettingsRepository:
    settings: dict[str, Any] = field(
        default_factory=lambda: {
            "theme": "system",
            "advancedMode": False,
            "defaultExportFormat": "wav",
            "defaultOutputDirectory": "/tmp/exports",
            "inferenceHost": "http://127.0.0.1:8765",
            "retentionDays": 14,
            "allowUnsafeVoiceCloning": False,
            "lastSelectedProfileId": "profile_001",
        }
    )

    def get_settings(self) -> dict[str, Any]:
        return dict(self.settings)

    def update_settings(self, patch: dict[str, Any]) -> dict[str, Any]:
        self.settings.update(patch)
        return dict(self.settings)


@dataclass
class FakeJobStore:
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)

    def seed_job(self, job_id: str, kind: str, label: str) -> dict[str, Any]:
        job = {
            "id": job_id,
            "kind": kind,
            "status": "completed",
            "progress": 100,
            "createdAt": "2026-03-23T00:00:00+00:00",
            "startedAt": "2026-03-23T00:00:00+00:00",
            "finishedAt": "2026-03-23T00:00:01+00:00",
            "request": {"label": label},
            "result": {"ok": True},
            "error": None,
            "artifacts": [_artifact(f"/tmp/{job_id}.wav", label=label)],
        }
        self.jobs[job_id] = job
        return job

    def list_jobs(self, *, kind: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        jobs = list(self.jobs.values())
        if kind is not None:
            jobs = [job for job in jobs if job["kind"] == kind]
        if status is not None:
            jobs = [job for job in jobs if job["status"] == status]
        return jobs[:limit]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        job = self.jobs[job_id]
        job["status"] = "cancelled"
        return {"id": job_id, "status": "cancelled"}


@dataclass
class FakeServices:
    health_service: Any
    tts_service: Any
    voice_conversion_service: Any
    isolation_service: Any
    profile_service: Any
    job_service: Any
    export_service: Any
    settings_service: Any

    async def shutdown(self) -> None:
        return None


@dataclass
class FakeHealthService:
    def __init__(self) -> None:
        self.paths = {
            "profiles": "/tmp/profiles",
            "exports": "/tmp/exports",
            "cache": "/tmp/cache",
        }

    async def get_health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "version": "0.1.0",
            "providers": [
                {"id": "tone_fallback", "label": "Tone Fallback", "available": True, "detail": "Test double"}
            ],
            "paths": self.paths,
            "diagnostics": {
                "ready": True,
                "dataRoot": "/tmp",
                "checks": [
                    {"id": "data_root", "label": "Data root", "ok": True, "detail": "/tmp"},
                    {"id": "profiles", "label": "Profiles directory", "ok": True, "detail": "/tmp/profiles"},
                    {"id": "exports", "label": "Exports directory", "ok": True, "detail": "/tmp/exports"},
                    {"id": "cache", "label": "Cache directory", "ok": True, "detail": "/tmp/cache"},
                    {"id": "jobs", "label": "Jobs cache", "ok": True, "detail": "/tmp/cache/jobs"},
                    {"id": "settings", "label": "Settings parent directory", "ok": True, "detail": "/tmp"},
                    {"id": "logs", "label": "Logs directory", "ok": True, "detail": "/tmp/logs"},
                ],
                "warnings": [],
            },
            "uptimeSeconds": 1.23,
        }


@dataclass
class FakeAcceptingService:
    store: FakeJobStore
    kind: str

    async def submit(self, request: Any) -> dict[str, Any]:
        index = len(self.store.jobs) + 1
        job_id = f"{self.kind}_{index:03d}"
        self.store.seed_job(job_id, self.kind, self.kind.replace("_", " ").title())
        return _accepted_job(self.kind, job_id)


@dataclass
class FakeExportService:
    async def export_artifact(self, request: Any) -> dict[str, Any]:
        payload = request.model_dump(by_alias=True)
        return _artifact(payload["destinationPath"], kind="export", label="Exported Audio")


class FakeSettingsService:
    def __init__(self, repository: FakeSettingsRepository) -> None:
        self.repository = repository

    async def get_settings(self) -> dict[str, Any]:
        return self.repository.get_settings()

    async def update_settings(self, request: Any) -> dict[str, Any]:
        return self.repository.update_settings(request.model_dump(by_alias=True))


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    profile_repo = FakeProfileRepository(
        profiles={
            "profile_001": {
                "id": "profile_001",
                "name": "Warm Narrator",
                "description": "Seed profile.",
                "consentConfirmed": True,
                "createdAt": "2026-03-23T00:00:00+00:00",
                "updatedAt": "2026-03-23T00:00:00+00:00",
                "embeddingStatus": "ready",
                "referenceClips": [],
                "defaultSettings": {
                    "speed": 1.0,
                    "strength": 0.65,
                    "pitchPreserve": True,
                    "cleanupLevel": 0.5,
                },
                "analysis": None,
            }
        }
    )
    job_store = FakeJobStore()
    job_store.seed_job("job_001", "tts", "Text To Speech")
    job_store.seed_job("job_002", "voice_conversion", "Voice Conversion")
    job_store.seed_job("job_003", "isolation", "Isolation")
    settings_repo = FakeSettingsRepository()

    class FakeJobService:
        async def list_jobs(self, kind: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
            return job_store.list_jobs(kind=kind, status=status, limit=limit)

        async def get_job(self, job_id: str) -> dict[str, Any] | None:
            return job_store.get_job(job_id)

        async def cancel_job(self, job_id: str) -> dict[str, Any]:
            return job_store.cancel_job(job_id)

    services = FakeServices(
        health_service=FakeHealthService(),
        tts_service=FakeAcceptingService(job_store, "tts"),
        voice_conversion_service=FakeAcceptingService(job_store, "voice_conversion"),
        isolation_service=FakeAcceptingService(job_store, "isolation"),
        profile_service=ProfileService(profile_repo),
        job_service=FakeJobService(),
        export_service=FakeExportService(),
        settings_service=FakeSettingsService(settings_repo),
    )

    monkeypatch.setattr(app.state, "services", services, raising=False)
    return TestClient(app)


def test_speak_text_contract(client: TestClient, tmp_path: Path) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["diagnostics"]["ready"] is True

    response = client.post(
        "/tts",
        json={
            "text": "Hello world",
            "profileId": "profile_001",
            "speed": 1.15,
            "preview": True,
            "outputFormat": "wav",
        },
    )
    assert response.status_code == 202
    payload = response.json()["job"]
    assert payload["kind"] == "tts"
    assert payload["pollUrl"] == f"/jobs/{payload['jobId']}"

    response = client.get("/jobs")
    assert response.status_code == 200
    assert response.json()["jobs"]

    response = client.get("/jobs/job_001")
    assert response.status_code == 200
    assert response.json()["id"] == "job_001"

    response = client.post("/jobs/job_001/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    response = client.post("/exports", json={"artifactPath": "/tmp/job_001.wav", "destinationPath": str(tmp_path / "export.wav"), "format": "wav"})
    assert response.status_code == 201
    assert response.json()["artifact"]["kind"] == "export"


def test_change_voice_contract(client: TestClient) -> None:
    response = client.post(
        "/voice-conversion",
        json={
            "inputPath": "/tmp/input.wav",
            "profileId": "profile_001",
            "strength": 0.6,
            "pitchPreserve": True,
            "preview": True,
            "outputFormat": "wav",
        },
    )
    assert response.status_code == 202
    payload = response.json()["job"]
    assert payload["kind"] == "voice_conversion"

    response = client.get("/profiles")
    assert response.status_code == 200
    assert response.json()["profiles"][0]["name"] == "Warm Narrator"

    response = client.patch("/profiles/profile_001", json={"name": "Updated Narrator"})
    assert response.status_code == 200
    assert response.json()["profile"]["name"] == "Updated Narrator"

    response = client.get("/settings")
    assert response.status_code == 200
    assert response.json()["settings"]["advancedMode"] is False

    response = client.put("/settings", json={"theme": "dark", "defaultOutputDirectory": "/tmp/out", "inferenceHost": "http://127.0.0.1:8765"})
    assert response.status_code == 200
    assert response.json()["settings"]["theme"] == "dark"


def test_clean_recording_contract_and_consent_guard(client: TestClient) -> None:
    response = client.post(
        "/isolation",
        json={
            "inputPath": "/tmp/noisy.wav",
            "mode": "voice_focus",
            "cleanupLevel": 0.7,
            "preview": True,
            "outputFormat": "wav",
        },
    )
    assert response.status_code == 202
    assert response.json()["job"]["kind"] == "isolation"

    response = client.post(
        "/profiles",
        json={
            "name": "Blocked Profile",
            "description": "Should fail.",
            "consentConfirmed": False,
            "referenceClipPaths": ["/tmp/reference.wav"],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "consent_required"
