export type JobKind = "tts" | "voice_conversion" | "isolation" | "waveform" | "export";

export type JobStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export type CleanupMode = "denoise" | "voice_focus" | "vocal_isolation";

export type OutputFormat = "wav" | "mp3";

export type EmbeddingStatus = "not_started" | "processing" | "ready" | "error";

export interface AudioArtifact {
  id: string;
  jobId?: string;
  kind: "input" | "preview" | "output" | "waveform" | "reference" | "export";
  label: string;
  path: string;
  format: string;
  durationMs: number;
  sampleRate: number;
  channels: number;
  createdAt: string;
}

export interface VoiceDefaults {
  speed: number;
  strength: number;
  pitchPreserve: boolean;
  cleanupLevel: number;
}

export interface VoiceProfile {
  id: string;
  name: string;
  description?: string;
  consentConfirmed: boolean;
  createdAt: string;
  updatedAt: string;
  embeddingStatus: EmbeddingStatus;
  referenceClips: AudioArtifact[];
  defaultSettings: VoiceDefaults;
  analysis?: {
    estimatedPitchHz?: number;
    averageLevelDb?: number;
    notes?: string;
  };
}

export interface AppSettings {
  theme: "system" | "light" | "dark";
  advancedMode: boolean;
  defaultExportFormat: OutputFormat;
  defaultOutputDirectory: string;
  inferenceHost: string;
  retentionDays: number;
  allowUnsafeVoiceCloning: boolean;
  lastSelectedProfileId?: string;
}

export interface StructuredError {
  code: string;
  message: string;
  details?: string;
  retryable?: boolean;
}

export interface ProcessingJob<Request = unknown, Result = unknown> {
  id: string;
  kind: JobKind;
  status: JobStatus;
  progress: number;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
  request: Request;
  result?: Result;
  error?: StructuredError;
  artifacts: AudioArtifact[];
}

export interface CreateProfileRequest {
  name: string;
  description?: string;
  consentConfirmed: boolean;
  referenceClipPaths: string[];
}

export interface TtsRequest {
  text: string;
  profileId: string;
  speed: number;
  preview: boolean;
  outputFormat: OutputFormat;
}

export interface VoiceConversionRequest {
  inputPath: string;
  profileId: string;
  strength: number;
  pitchPreserve: boolean;
  preview: boolean;
  outputFormat: OutputFormat;
}

export interface IsolationRequest {
  inputPath: string;
  mode: CleanupMode;
  cleanupLevel: number;
  preview: boolean;
  outputFormat: OutputFormat;
}

export interface ExportRequest {
  artifactPath: string;
  destinationPath: string;
  format: OutputFormat;
}

export interface ProviderCapability {
  id: string;
  label: string;
  available: boolean;
  detail?: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  version: string;
  providers: ProviderCapability[];
  paths: {
    profiles: string;
    exports: string;
    cache: string;
  };
  uptimeSeconds?: number;
}
