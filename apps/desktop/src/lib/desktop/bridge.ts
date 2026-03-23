import { invoke } from "@tauri-apps/api/core";
import type {
  AppSettings,
  AudioArtifact,
  CreateProfileRequest,
  ExportRequest,
  HealthResponse,
  IsolationRequest,
  JobStatus,
  ProcessingJob,
  TtsRequest,
  VoiceConversionRequest,
  VoiceProfile,
} from "@home-voice-studio/shared-types";
import type {
  AcceptedJob,
  ExportArtifactResponse,
  DesktopPaths,
  DesktopSaveDialogRequest,
  DesktopSidecarRequest,
  JobsResponse,
  ProfileMutationResponse,
  ProfilesResponse,
  SettingsResponse,
  SidecarStatus,
} from "./types";

const COMMANDS = {
  getPaths: "get_app_paths",
  pickAudioFile: "pick_audio_file",
  pickAudioFiles: "pick_audio_files",
  saveExportFile: "save_export_file",
  confirmVoiceCloning: "confirm_voice_cloning",
  ensureSidecar: "ensure_sidecar_running",
  sidecarHealth: "sidecar_health",
  callSidecarRoute: "call_sidecar_route",
} as const;

export async function getDesktopPaths(): Promise<DesktopPaths> {
  return invoke<DesktopPaths>(COMMANDS.getPaths);
}

export async function pickAudioFile(): Promise<string | null> {
  return invoke<string | null>(COMMANDS.pickAudioFile);
}

export async function pickAudioFiles(): Promise<string[]> {
  return invoke<string[]>(COMMANDS.pickAudioFiles);
}

export async function saveExportFile(
  request: DesktopSaveDialogRequest,
): Promise<string | null> {
  return invoke<string | null>(COMMANDS.saveExportFile, { request });
}

export async function confirmVoiceCloning(): Promise<boolean> {
  return invoke<boolean>(COMMANDS.confirmVoiceCloning);
}

export async function ensureSidecarRunning(): Promise<SidecarStatus> {
  return invoke<SidecarStatus>(COMMANDS.ensureSidecar);
}

export async function getSidecarHealth(): Promise<HealthResponse> {
  return invoke<HealthResponse>(COMMANDS.sidecarHealth);
}

export async function requestSidecarRoute<TResponse>(
  request: DesktopSidecarRequest,
): Promise<TResponse> {
  return invoke<TResponse>(COMMANDS.callSidecarRoute, { request });
}

export async function requestTts(request: TtsRequest): Promise<AcceptedJob> {
  const response = await requestSidecarRoute<{ job: AcceptedJob }>({
    method: "POST",
    path: "/tts",
    body: request,
  });
  return response.job;
}

export async function requestVoiceConversion(
  request: VoiceConversionRequest,
): Promise<AcceptedJob> {
  const response = await requestSidecarRoute<{ job: AcceptedJob }>({
    method: "POST",
    path: "/voice-conversion",
    body: request,
  });
  return response.job;
}

export async function requestIsolation(request: IsolationRequest): Promise<AcceptedJob> {
  const response = await requestSidecarRoute<{ job: AcceptedJob }>({
    method: "POST",
    path: "/isolation",
    body: request,
  });
  return response.job;
}

export async function listProfiles(): Promise<VoiceProfile[]> {
  const response = await requestSidecarRoute<ProfilesResponse>({
    method: "GET",
    path: "/profiles",
  });
  return response.profiles;
}

export async function createProfile(request: CreateProfileRequest): Promise<VoiceProfile> {
  const response = await requestSidecarRoute<ProfileMutationResponse>({
    method: "POST",
    path: "/profiles",
    body: request,
  });
  return response.profile;
}

export async function listJobs(): Promise<ProcessingJob[]> {
  const response = await requestSidecarRoute<JobsResponse>({
    method: "GET",
    path: "/jobs",
  });
  return response.jobs;
}

export async function getJob(jobId: string): Promise<ProcessingJob> {
  return requestSidecarRoute<ProcessingJob>({
    method: "GET",
    path: `/jobs/${encodeURIComponent(jobId)}`,
  });
}

export async function cancelJob(jobId: string): Promise<{ id: string; status: JobStatus }> {
  return requestSidecarRoute<{ id: string; status: JobStatus }>({
    method: "POST",
    path: `/jobs/${encodeURIComponent(jobId)}/cancel`,
  });
}

export async function getSettings(): Promise<AppSettings> {
  const response = await requestSidecarRoute<SettingsResponse>({
    method: "GET",
    path: "/settings",
  });
  return response.settings;
}

export async function updateSettings(request: AppSettings): Promise<AppSettings> {
  const response = await requestSidecarRoute<SettingsResponse>({
    method: "PUT",
    path: "/settings",
    body: request,
  });
  return response.settings;
}

export async function exportArtifact(request: ExportRequest): Promise<AudioArtifact> {
  const response = await requestSidecarRoute<ExportArtifactResponse>({
    method: "POST",
    path: "/exports",
    body: request,
  });
  return response.artifact;
}
