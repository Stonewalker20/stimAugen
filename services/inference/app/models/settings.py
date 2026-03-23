from __future__ import annotations

from pydantic import Field

from app.models.common import ApiModel


class AppSettings(ApiModel):
    theme: str = "system"
    advanced_mode: bool = Field(default=False, alias="advancedMode")
    default_export_format: str = Field(default="wav", alias="defaultExportFormat")
    default_output_directory: str = Field(alias="defaultOutputDirectory")
    inference_host: str = Field(alias="inferenceHost")
    retention_days: int = Field(default=14, alias="retentionDays")
    allow_unsafe_voice_cloning: bool = Field(default=False, alias="allowUnsafeVoiceCloning")
    last_selected_profile_id: str | None = Field(default=None, alias="lastSelectedProfileId")


class SettingsResponse(ApiModel):
    settings: AppSettings
