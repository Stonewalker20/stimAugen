import type {
  AppSettings,
  AudioArtifact,
  CleanupMode,
  HealthResponse,
  ProcessingJob,
  VoiceProfile,
} from "@home-voice-studio/shared-types";

const now = new Date().toISOString();

export interface DemoStore {
  health: HealthResponse;
  profiles: VoiceProfile[];
  jobs: ProcessingJob[];
  settings: AppSettings;
}

const previewArtifact = (overrides: Partial<AudioArtifact>): AudioArtifact => ({
  id: crypto.randomUUID(),
  kind: "preview",
  label: "Preview",
  path: "/tmp/mock-preview.wav",
  format: "wav",
  durationMs: 8200,
  sampleRate: 22050,
  channels: 1,
  createdAt: now,
  ...overrides,
});

export const demoProfiles: VoiceProfile[] = [
  {
    id: "profile-summer",
    name: "Summer Narrator",
    description: "Warm, steady voice profile for everyday prompts.",
    consentConfirmed: true,
    createdAt: now,
    updatedAt: now,
    embeddingStatus: "ready",
    referenceClips: [
      previewArtifact({
        id: "artifact-summer-ref",
        kind: "reference",
        label: "Kitchen note reference",
        path: "data/profiles/profile-summer/reference.wav",
      }),
    ],
    defaultSettings: {
      speed: 1,
      strength: 0.62,
      pitchPreserve: true,
      cleanupLevel: 0.55,
    },
    analysis: {
      estimatedPitchHz: 201,
      averageLevelDb: -17.2,
      notes: "Balanced tone with clear mids.",
    },
  },
  {
    id: "profile-midnight",
    name: "Midnight Story",
    description: "Lower, softer tone suited for bedtime narration.",
    consentConfirmed: true,
    createdAt: now,
    updatedAt: now,
    embeddingStatus: "processing",
    referenceClips: [
      previewArtifact({
        id: "artifact-midnight-ref",
        kind: "reference",
        label: "Living room memo",
        path: "data/profiles/profile-midnight/reference.wav",
      }),
    ],
    defaultSettings: {
      speed: 0.92,
      strength: 0.7,
      pitchPreserve: true,
      cleanupLevel: 0.46,
    },
  },
];

export const demoJobs: ProcessingJob[] = [
  {
    id: "job-tts-demo",
    kind: "tts",
    status: "completed",
    progress: 100,
    createdAt: now,
    startedAt: now,
    finishedAt: now,
    request: {
      text: "Dinner is ready in ten minutes.",
      profileId: "profile-summer",
      speed: 1,
      preview: true,
      outputFormat: "wav",
    },
    artifacts: [
      previewArtifact({
        id: "artifact-job-tts",
        label: "Dinner reminder",
        path: "data/cache/jobs/job-tts-demo/output.wav",
      }),
    ],
  },
  {
    id: "job-clean-demo",
    kind: "isolation",
    status: "running",
    progress: 52,
    createdAt: now,
    startedAt: now,
    request: {
      inputPath: "/Users/demo/Desktop/porch-note.wav",
      mode: "voice_focus",
      cleanupLevel: 0.61,
      preview: true,
      outputFormat: "wav",
    },
    artifacts: [],
  },
];

export const demoSettings: AppSettings = {
  theme: "system",
  advancedMode: false,
  defaultExportFormat: "wav",
  defaultOutputDirectory: "data/exports",
  inferenceHost: "http://127.0.0.1:8404",
  retentionDays: 21,
  allowUnsafeVoiceCloning: false,
  lastSelectedProfileId: demoProfiles[0].id,
};

export const demoHealth: HealthResponse = {
  status: "degraded",
  version: "0.1.0-dev",
  providers: [
    {
      id: "tts-native",
      label: "Local speech engine",
      available: true,
      detail: "OS-native voice output is available.",
    },
    {
      id: "conversion-dsp",
      label: "Offline voice conversion",
      available: true,
      detail: "DSP conversion is active. Model plug-ins can be added later.",
    },
    {
      id: "ffmpeg",
      label: "FFmpeg audio toolkit",
      available: false,
      detail: "Optional. MP3 export and deeper cleanup improve when installed.",
    },
  ],
  paths: {
    profiles: "data/profiles",
    exports: "data/exports",
    cache: "data/cache",
  },
  uptimeSeconds: 42,
};

export const cleanupModeLabels: Record<CleanupMode, string> = {
  denoise: "Denoise",
  voice_focus: "Voice Focus",
  vocal_isolation: "Vocal Isolation",
};

export function createDemoStore(): DemoStore {
  return {
    health: demoHealth,
    profiles: demoProfiles,
    jobs: demoJobs,
    settings: demoSettings,
  };
}
