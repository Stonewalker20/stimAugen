import { convertFileSrc } from "@tauri-apps/api/core";
import type {
  AppSettings,
  AudioArtifact,
  CreateProfileRequest,
  ExportRequest,
  HealthResponse,
  IsolationRequest,
  ProcessingJob,
  TtsRequest,
  VoiceConversionRequest,
  VoiceProfile,
} from "@home-voice-studio/shared-types";
import * as desktop from "./desktop";
import {
  createDemoStore,
  type DemoStore,
} from "./mock-data";

interface RuntimeBridge {
  getHealth(): Promise<HealthResponse>;
  getProfiles(): Promise<VoiceProfile[]>;
  createProfile(request: CreateProfileRequest): Promise<VoiceProfile>;
  getJobs(): Promise<ProcessingJob[]>;
  getSettings(): Promise<AppSettings>;
  saveSettings(settings: AppSettings): Promise<AppSettings>;
  submitTts(request: TtsRequest): Promise<ProcessingJob<TtsRequest>>;
  submitVoiceConversion(
    request: VoiceConversionRequest,
  ): Promise<ProcessingJob<VoiceConversionRequest>>;
  submitIsolation(
    request: IsolationRequest,
  ): Promise<ProcessingJob<IsolationRequest>>;
  exportArtifact(request: ExportRequest): Promise<AudioArtifact>;
}

interface AcceptedJobLike {
  jobId: string;
  kind: string;
  status: string;
  progress: number;
  createdAt: string;
  pollUrl: string;
}

declare global {
  interface Window {
    __HOME_VOICE_BRIDGE__?: RuntimeBridge;
    __TAURI_INTERNALS__?: unknown;
  }
}

const pause = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

const STORE_KEY = "home-voice-studio-demo-store";
const LOCAL_HTTP_BASE = "http://127.0.0.1:8765";

function loadStore(): DemoStore {
  const raw = window.localStorage.getItem(STORE_KEY);
  if (!raw) {
    const seed = createDemoStore();
    saveStore(seed);
    return seed;
  }

  try {
    return JSON.parse(raw) as DemoStore;
  } catch {
    const seed = createDemoStore();
    saveStore(seed);
    return seed;
  }
}

function saveStore(store: DemoStore) {
  window.localStorage.setItem(STORE_KEY, JSON.stringify(store));
}

function isLocalHttpBase(value: string) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" && ["localhost", "127.0.0.1", "::1"].includes(parsed.hostname);
  } catch {
    return false;
  }
}

function upsertJob(store: DemoStore, job: ProcessingJob) {
  store.jobs = [job, ...store.jobs.filter((existing) => existing.id !== job.id)];
  saveStore(store);
}

function makeAudioArtifact(
  jobId: string,
  label: string,
  format: "wav" | "mp3",
  suffix: string,
  durationMs: number,
) {
  return {
    id: crypto.randomUUID(),
    jobId,
    kind: "output" as const,
    label,
    path: `data/cache/jobs/${jobId}/${suffix}.${format}`,
    format,
    durationMs,
    sampleRate: 24000,
    channels: 1,
    createdAt: new Date().toISOString(),
  };
}

function acceptedToJob<Request>(accepted: AcceptedJobLike, request: Request): ProcessingJob<Request> {
  return {
    id: accepted.jobId,
    kind: accepted.kind as ProcessingJob<Request>["kind"],
    status: accepted.status as ProcessingJob<Request>["status"],
    progress: accepted.progress,
    createdAt: accepted.createdAt,
    request,
    artifacts: [],
  };
}

function scheduleCompletion(
  job: ProcessingJob,
  updater: (current: ProcessingJob) => ProcessingJob,
  delayMs: number,
) {
  window.setTimeout(() => {
    const store = loadStore();
    const current = store.jobs.find((entry) => entry.id === job.id);
    if (!current || current.status === "cancelled") {
      return;
    }
    upsertJob(store, updater(current));
  }, delayMs);
}

const mockBridge: RuntimeBridge = {
  async getHealth() {
    await pause(120);
    return loadStore().health;
  },
  async getProfiles() {
    await pause(120);
    return loadStore().profiles;
  },
  async createProfile(request) {
    await pause(300);
    const store = loadStore();
    const now = new Date().toISOString();
    const profile: VoiceProfile = {
      id: `profile-${crypto.randomUUID()}`,
      name: request.name,
      description: request.description,
      consentConfirmed: request.consentConfirmed,
      createdAt: now,
      updatedAt: now,
      embeddingStatus: "processing",
      referenceClips: request.referenceClipPaths.map((path, index) => ({
        id: `artifact-${index}-${crypto.randomUUID()}`,
        kind: "reference",
        label: `Reference clip ${index + 1}`,
        path,
        format: path.endsWith(".mp3") ? "mp3" : "wav",
        durationMs: 5400,
        sampleRate: 44100,
        channels: 1,
        createdAt: now,
      })),
      defaultSettings: {
        speed: 1,
        strength: 0.65,
        pitchPreserve: true,
        cleanupLevel: 0.5,
      },
    };
    store.profiles = [profile, ...store.profiles];
    store.settings.lastSelectedProfileId = profile.id;
    saveStore(store);
    return profile;
  },
  async getJobs() {
    await pause(120);
    return loadStore().jobs;
  },
  async getSettings() {
    await pause(120);
    return loadStore().settings;
  },
  async saveSettings(settings) {
    await pause(120);
    const store = loadStore();
    store.settings = settings;
    saveStore(store);
    return settings;
  },
  async submitTts(request) {
    await pause(180);
    const store = loadStore();
    const createdAt = new Date().toISOString();
    const job: ProcessingJob<TtsRequest> = {
      id: `job-tts-${crypto.randomUUID()}`,
      kind: "tts",
      status: "running",
      progress: 22,
      createdAt,
      startedAt: createdAt,
      request,
      artifacts: [],
    };
    upsertJob(store, job);
    scheduleCompletion(
      job,
      (current) => ({
        ...current,
        status: "completed",
        progress: 100,
        finishedAt: new Date().toISOString(),
        artifacts: [
          makeAudioArtifact(
            current.id,
            request.preview ? "Speech preview" : "Speech output",
            request.outputFormat,
            "tts-output",
            Math.max(2500, request.text.length * 95),
          ),
        ],
      }),
      1200,
    );
    return job;
  },
  async submitVoiceConversion(request) {
    await pause(180);
    const store = loadStore();
    const createdAt = new Date().toISOString();
    const job: ProcessingJob<VoiceConversionRequest> = {
      id: `job-vc-${crypto.randomUUID()}`,
      kind: "voice_conversion",
      status: "running",
      progress: 18,
      createdAt,
      startedAt: createdAt,
      request,
      artifacts: [],
    };
    upsertJob(store, job);
    scheduleCompletion(
      job,
      (current) => ({
        ...current,
        status: "completed",
        progress: 100,
        finishedAt: new Date().toISOString(),
        artifacts: [
          makeAudioArtifact(
            current.id,
            request.preview ? "Converted preview" : "Converted output",
            request.outputFormat,
            "conversion-output",
            6800,
          ),
        ],
      }),
      1500,
    );
    return job;
  },
  async submitIsolation(request) {
    await pause(180);
    const store = loadStore();
    const createdAt = new Date().toISOString();
    const job: ProcessingJob<IsolationRequest> = {
      id: `job-iso-${crypto.randomUUID()}`,
      kind: "isolation",
      status: "running",
      progress: 16,
      createdAt,
      startedAt: createdAt,
      request,
      artifacts: [],
    };
    upsertJob(store, job);
    scheduleCompletion(
      job,
      (current) => ({
        ...current,
        status: "completed",
        progress: 100,
        finishedAt: new Date().toISOString(),
        artifacts: [
          makeAudioArtifact(
            current.id,
            request.preview ? "Cleanup preview" : "Cleanup output",
            request.outputFormat,
            "cleanup-output",
            7200,
          ),
        ],
      }),
      1350,
    );
    return job;
  },
  async exportArtifact(request) {
    await pause(280);
    const store = loadStore();
    const artifact = makeAudioArtifact(
      `export-${crypto.randomUUID()}`,
      "Exported file",
      request.format,
      `exports/${request.destinationPath.split("/").pop()?.replace(/\.[^.]+$/, "") ?? "audio"}`,
      6400,
    );
    const exportJob: ProcessingJob<ExportRequest> = {
      id: `job-export-${crypto.randomUUID()}`,
      kind: "export",
      status: "completed",
      progress: 100,
      createdAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
      finishedAt: new Date().toISOString(),
      request,
      artifacts: [artifact],
    };
    upsertJob(store, exportJob);
    return artifact;
  },
};

function isTauriHost() {
  return typeof window !== "undefined" && typeof window.__TAURI_INTERNALS__ !== "undefined";
}

function getHttpBaseUrl() {
  const stored = window.localStorage.getItem("home-voice-studio-http-base");
  if (stored && isLocalHttpBase(stored)) {
    return stored;
  }
  if (stored) {
    window.localStorage.setItem("home-voice-studio-http-base", LOCAL_HTTP_BASE);
  }
  return LOCAL_HTTP_BASE;
}

async function requestHttp<TResponse>(method: string, path: string, body?: unknown): Promise<TResponse> {
  const response = await fetch(`${getHttpBaseUrl()}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} for ${path}`);
  }
  return (await response.json()) as TResponse;
}

async function withFallback<T>(primary: () => Promise<T>, fallback: () => Promise<T>): Promise<T> {
  try {
    return await primary();
  } catch {
    return fallback();
  }
}

const httpBridge: RuntimeBridge = {
  async getHealth() {
    return requestHttp<HealthResponse>("GET", "/health");
  },
  async getProfiles() {
    const response = await requestHttp<{ profiles: VoiceProfile[] }>("GET", "/profiles");
    return response.profiles;
  },
  async createProfile(request) {
    const response = await requestHttp<{ profile: VoiceProfile }>("POST", "/profiles", request);
    return response.profile;
  },
  async getJobs() {
    const response = await requestHttp<{ jobs: ProcessingJob[] }>("GET", "/jobs");
    return response.jobs;
  },
  async getSettings() {
    const response = await requestHttp<{ settings: AppSettings }>("GET", "/settings");
    return response.settings;
  },
  async saveSettings(settings) {
    const response = await requestHttp<{ settings: AppSettings }>("PUT", "/settings", settings);
    return response.settings;
  },
  async submitTts(request) {
    const response = await requestHttp<{ job: AcceptedJobLike }>("POST", "/tts", request);
    return acceptedToJob(response.job, request);
  },
  async submitVoiceConversion(request) {
    const response = await requestHttp<{ job: AcceptedJobLike }>("POST", "/voice-conversion", request);
    return acceptedToJob(response.job, request);
  },
  async submitIsolation(request) {
    const response = await requestHttp<{ job: AcceptedJobLike }>("POST", "/isolation", request);
    return acceptedToJob(response.job, request);
  },
  async exportArtifact(request) {
    const response = await requestHttp<{ artifact: AudioArtifact }>("POST", "/exports", request);
    return response.artifact;
  },
};

const desktopBridge: RuntimeBridge = {
  async getHealth() {
    await desktop.ensureSidecarRunning();
    return desktop.getSidecarHealth();
  },
  async getProfiles() {
    await desktop.ensureSidecarRunning();
    return desktop.listProfiles();
  },
  async createProfile(request) {
    await desktop.ensureSidecarRunning();
    if (request.consentConfirmed) {
      const confirmed = await desktop.confirmVoiceCloning();
      if (!confirmed) {
        throw new Error("Voice cloning consent was not confirmed.");
      }
    }
    return desktop.createProfile(request);
  },
  async getJobs() {
    await desktop.ensureSidecarRunning();
    return desktop.listJobs();
  },
  async getSettings() {
    await desktop.ensureSidecarRunning();
    return desktop.getSettings();
  },
  async saveSettings(settings) {
    await desktop.ensureSidecarRunning();
    return desktop.updateSettings(settings);
  },
  async submitTts(request) {
    await desktop.ensureSidecarRunning();
    return acceptedToJob(await desktop.requestTts(request), request);
  },
  async submitVoiceConversion(request) {
    await desktop.ensureSidecarRunning();
    return acceptedToJob(await desktop.requestVoiceConversion(request), request);
  },
  async submitIsolation(request) {
    await desktop.ensureSidecarRunning();
    return acceptedToJob(await desktop.requestIsolation(request), request);
  },
  async exportArtifact(request) {
    await desktop.ensureSidecarRunning();
    return desktop.exportArtifact(request);
  },
};

const browserBridge: RuntimeBridge = {
  getHealth: () => withFallback(() => httpBridge.getHealth(), () => mockBridge.getHealth()),
  getProfiles: () => withFallback(() => httpBridge.getProfiles(), () => mockBridge.getProfiles()),
  createProfile: (request) => withFallback(() => httpBridge.createProfile(request), () => mockBridge.createProfile(request)),
  getJobs: () => withFallback(() => httpBridge.getJobs(), () => mockBridge.getJobs()),
  getSettings: () => withFallback(() => httpBridge.getSettings(), () => mockBridge.getSettings()),
  saveSettings: (settings) => withFallback(() => httpBridge.saveSettings(settings), () => mockBridge.saveSettings(settings)),
  submitTts: (request) => withFallback(() => httpBridge.submitTts(request), () => mockBridge.submitTts(request)),
  submitVoiceConversion: (request) =>
    withFallback(() => httpBridge.submitVoiceConversion(request), () => mockBridge.submitVoiceConversion(request)),
  submitIsolation: (request) =>
    withFallback(() => httpBridge.submitIsolation(request), () => mockBridge.submitIsolation(request)),
  exportArtifact: (request) =>
    withFallback(() => httpBridge.exportArtifact(request), () => mockBridge.exportArtifact(request)),
};

export const runtime = window.__HOME_VOICE_BRIDGE__ ?? (isTauriHost() ? desktopBridge : browserBridge);

export async function chooseAudioFile(): Promise<string | null> {
  if (!isTauriHost()) {
    return null;
  }
  return desktop.pickAudioFile();
}

export async function chooseAudioFiles(): Promise<string[]> {
  if (!isTauriHost()) {
    return [];
  }
  return desktop.pickAudioFiles();
}

export async function chooseExportDestination(
  defaultName: string,
  defaultDirectory?: string,
): Promise<string | null> {
  if (!isTauriHost()) {
    return defaultDirectory ? `${defaultDirectory}/${defaultName}` : defaultName;
  }
  return desktop.saveExportFile({
    title: "Export Audio",
    defaultName,
    defaultDirectory,
    filters: [
      { name: "Wave Audio", extensions: ["wav"] },
      { name: "MP3 Audio", extensions: ["mp3"] },
    ],
  });
}

export function resolveArtifactUrl(path: string): string {
  if (!path) {
    return path;
  }
  return isTauriHost() ? convertFileSrc(path) : path;
}
