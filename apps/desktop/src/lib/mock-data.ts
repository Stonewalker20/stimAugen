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
    id: "sample_warm_narrator",
    name: "Warm Narrator",
    description: "Steady everyday voice for reminders, timers, and home notices.",
    consentConfirmed: true,
    createdAt: now,
    updatedAt: now,
    embeddingStatus: "ready",
    referenceClips: [
      previewArtifact({
        id: "artifact-summer-ref",
        kind: "reference",
        label: "Kitchen note reference",
        path: "data/profiles/sample_warm_narrator/references/warm-narrator.wav",
      }),
    ],
    defaultSettings: {
      speed: 1,
      strength: 0.55,
      pitchPreserve: true,
      cleanupLevel: 0.5,
    },
    analysis: {
      estimatedPitchHz: 220,
      averageLevelDb: -18,
      notes: "Balanced and friendly. Good default for general home speech.",
    },
  },
  {
    id: "sample-soft-announce",
    name: "Soft Announcer",
    description: "Gentler voice for bedtime, calm prompts, and ambient playback.",
    consentConfirmed: true,
    createdAt: now,
    updatedAt: now,
    embeddingStatus: "ready",
    referenceClips: [
      previewArtifact({
        id: "artifact-midnight-ref",
        kind: "reference",
        label: "Living room memo",
        path: "data/profiles/sample-soft-announce/references/soft-announce.wav",
      }),
    ],
    defaultSettings: {
      speed: 0.92,
      strength: 0.48,
      pitchPreserve: true,
      cleanupLevel: 0.42,
    },
    analysis: {
      estimatedPitchHz: 198,
      averageLevelDb: -19,
      notes: "Softer and slower. Good for low-pressure prompts and story mode.",
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
      profileId: "sample_warm_narrator",
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
  inferenceHost: "http://127.0.0.1:8765",
  retentionDays: 21,
  allowUnsafeVoiceCloning: false,
  lastSelectedProfileId: demoProfiles[0].id,
};

export const demoHealth: HealthResponse = {
  status: "ok",
  version: "0.1.0-dev",
  providers: [
    {
      id: "speech_generation",
      label: "Speak Text",
      available: true,
      required: true,
      detail: "Built-in local speech is ready.",
    },
    {
      id: "voice_change",
      label: "Change Voice",
      available: true,
      required: true,
      detail: "Offline voice change is ready for uploaded recordings.",
    },
    {
      id: "clean_recording",
      label: "Clean Recording",
      available: true,
      required: true,
      detail: "Cleanup modes are ready for local denoise and voice focus.",
    },
    {
      id: "mp3_export",
      label: "MP3 Export",
      available: false,
      required: false,
      detail: "Optional. Install FFmpeg if you want MP3 export.",
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
