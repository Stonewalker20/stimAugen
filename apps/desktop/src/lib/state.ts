import { useEffect, useState } from "react";
import type {
  AppSettings,
  CreateProfileRequest,
  ExportRequest,
  HealthResponse,
  IsolationRequest,
  ProcessingJob,
  TtsRequest,
  VoiceConversionRequest,
  VoiceProfile,
} from "@home-voice-studio/shared-types";
import { runtime } from "./runtime";

export interface WorkspaceState {
  health?: HealthResponse;
  profiles: VoiceProfile[];
  jobs: ProcessingJob[];
  settings?: AppSettings;
  selectedProfileId?: string;
  loading: boolean;
  refreshing: boolean;
  error?: string;
}

const pushJob = (jobs: ProcessingJob[], job: ProcessingJob): ProcessingJob[] => [
  job,
  ...jobs.filter((existing) => existing.id !== job.id),
];

export function useWorkspaceState() {
  const [state, setState] = useState<WorkspaceState>({
    profiles: [],
    jobs: [],
    loading: true,
    refreshing: false,
  });

  const refresh = async () => {
    setState((current) => ({ ...current, refreshing: true }));

    try {
      const [health, profiles, jobs, settings] = await Promise.all([
        runtime.getHealth(),
        runtime.getProfiles(),
        runtime.getJobs(),
        runtime.getSettings(),
      ]);
      setState({
        health,
        profiles,
        jobs,
        settings,
        selectedProfileId: settings.lastSelectedProfileId ?? profiles[0]?.id,
        loading: false,
        refreshing: false,
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        loading: false,
        refreshing: false,
        error: error instanceof Error ? error.message : "Unable to load the studio.",
      }));
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    const shouldPoll = state.jobs.some((job) => job.status === "queued" || job.status === "running");
    if (!shouldPoll) {
      return;
    }

    const timer = window.setInterval(() => {
      void runtime.getJobs().then((jobs) => {
        setState((current) => ({
          ...current,
          jobs,
        }));
      });
    }, 1200);

    return () => window.clearInterval(timer);
  }, [state.jobs]);

  const createProfile = async (request: CreateProfileRequest) => {
    const profile = await runtime.createProfile(request);
    setState((current) => ({
      ...current,
      profiles: [profile, ...current.profiles],
      selectedProfileId: profile.id,
    }));
    return profile;
  };

  const submitTts = async (request: TtsRequest) => {
    const job = await runtime.submitTts(request);
    setState((current) => ({
      ...current,
      jobs: pushJob(current.jobs, job),
    }));
    return job;
  };

  const submitVoiceConversion = async (request: VoiceConversionRequest) => {
    const job = await runtime.submitVoiceConversion(request);
    setState((current) => ({
      ...current,
      jobs: pushJob(current.jobs, job),
    }));
    return job;
  };

  const submitIsolation = async (request: IsolationRequest) => {
    const job = await runtime.submitIsolation(request);
    setState((current) => ({
      ...current,
      jobs: pushJob(current.jobs, job),
    }));
    return job;
  };

  const saveSettings = async (settings: AppSettings) => {
    const saved = await runtime.saveSettings(settings);
    setState((current) => ({
      ...current,
      settings: saved,
    }));
    return saved;
  };

  const exportArtifact = async (request: ExportRequest) => runtime.exportArtifact(request);

  return {
    state,
    refresh,
    createProfile,
    submitTts,
    submitVoiceConversion,
    submitIsolation,
    saveSettings,
    exportArtifact,
    setSelectedProfileId(profileId?: string) {
      let nextSettings: AppSettings | undefined;
      setState((current) => {
        nextSettings = current.settings
          ? { ...current.settings, lastSelectedProfileId: profileId }
          : current.settings;
        return {
          ...current,
          selectedProfileId: profileId,
          settings: nextSettings,
        };
      });

      if (nextSettings) {
        void runtime.saveSettings(nextSettings).then((saved) => {
          setState((current) => ({
            ...current,
            settings: saved,
          }));
        });
      }
    },
  };
}
