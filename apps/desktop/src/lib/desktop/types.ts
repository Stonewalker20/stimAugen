import type {
  AppSettings,
  AudioArtifact,
  CleanupMode,
  CreateProfileRequest,
  ExportRequest,
  HealthResponse,
  IsolationRequest,
  JobKind,
  JobStatus,
  OutputFormat,
  ProcessingJob,
  TtsRequest,
  VoiceConversionRequest,
  VoiceProfile,
} from "@home-voice-studio/shared-types";

export type {
  AppSettings,
  AudioArtifact,
  CleanupMode,
  CreateProfileRequest,
  ExportRequest,
  HealthResponse,
  IsolationRequest,
  JobKind,
  JobStatus,
  OutputFormat,
  ProcessingJob,
  TtsRequest,
  VoiceConversionRequest,
  VoiceProfile,
} from "@home-voice-studio/shared-types";

export interface DesktopPaths {
  dataRoot: string;
  profilesDir: string;
  exportsDir: string;
  cacheDir: string;
  logsDir: string;
  tempDir: string;
  isDevelopment: boolean;
}

export interface DesktopDialogFilter {
  name: string;
  extensions: string[];
}

export interface DesktopSaveDialogRequest {
  title?: string;
  defaultName?: string;
  defaultDirectory?: string;
  filters?: DesktopDialogFilter[];
}

export interface DesktopSidecarRequest {
  method: string;
  path: string;
  body?: unknown;
}

export interface SidecarStatus {
  running: boolean;
  baseUrl: string;
  host: string;
  port: number;
}

export interface DesktopCommandEnvelope<T = unknown> {
  command: string;
  args?: Record<string, unknown>;
  result: T;
}

export interface AcceptedJob {
  jobId: string;
  kind: string;
  status: string;
  progress: number;
  createdAt: string;
  pollUrl: string;
}

export interface ProfilesResponse {
  profiles: VoiceProfile[];
}

export interface ProfileMutationResponse {
  profile: VoiceProfile;
}

export interface JobsResponse {
  jobs: ProcessingJob[];
}

export interface SettingsResponse {
  settings: AppSettings;
}

export interface ExportArtifactResponse {
  artifact: AudioArtifact;
}
