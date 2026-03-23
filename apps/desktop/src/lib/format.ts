import type { CleanupMode, JobStatus } from "@home-voice-studio/shared-types";

export function formatStatus(status: JobStatus) {
  switch (status) {
    case "queued":
      return "Queued";
    case "running":
      return "Running";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    case "cancelled":
      return "Cancelled";
    default:
      return status;
  }
}

export function formatCleanupMode(mode: CleanupMode) {
  switch (mode) {
    case "denoise":
      return "Denoise";
    case "voice_focus":
      return "Voice Focus";
    case "vocal_isolation":
      return "Vocal Isolation";
    default:
      return mode;
  }
}

export function formatRelativeDate(iso: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(iso));
}
