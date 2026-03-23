import { Badge, Card, ProgressBar, SectionTitle } from "@home-voice-studio/ui";
import type {
  AppSettings,
  AudioArtifact,
  HealthResponse,
  ProcessingJob,
  VoiceProfile,
} from "@home-voice-studio/shared-types";
import { formatRelativeDate, formatStatus } from "@/lib/format";
import { resolveArtifactUrl } from "@/lib/runtime";

export function ResultPreview({
  title,
  artifact,
  secondaryText,
  onExport,
  exportBusy = false,
}: {
  title: string;
  artifact?: AudioArtifact;
  secondaryText?: string;
  onExport?: () => void;
  exportBusy?: boolean;
}) {
  return (
    <Card>
      <SectionTitle title={title} subtitle={secondaryText ?? "Latest output"} compact />
      {artifact ? (
        <div className="result-stack">
          <div className="audio-card">
            <div>
              <p className="audio-title">{artifact.label}</p>
              <p className="muted">
                {artifact.format.toUpperCase()} • {(artifact.durationMs / 1000).toFixed(1)}s •{" "}
                {artifact.sampleRate} Hz
              </p>
            </div>
            <audio controls preload="none" className="audio-player">
              <source src={resolveArtifactUrl(artifact.path)} />
            </audio>
          </div>
          {onExport ? (
            <div className="result-actions">
              <button
                type="button"
                className="inline-action"
                onClick={onExport}
                disabled={exportBusy}
              >
                {exportBusy ? "Exporting…" : "Quick Export"}
              </button>
            </div>
          ) : null}
          <code className="path-pill">{artifact.path}</code>
        </div>
      ) : (
        <p className="muted">No result yet. Start a job to see the preview here.</p>
      )}
    </Card>
  );
}

export function ProfileStrip({
  profiles,
  selectedProfileId,
  onSelect,
}: {
  profiles: VoiceProfile[];
  selectedProfileId?: string;
  onSelect(profileId: string): void;
}) {
  return (
    <Card>
      <SectionTitle title="Voice Profiles" subtitle="Saved voices available to all workflows" compact />
      <div className="profile-strip">
        {profiles.map((profile) => (
          <button
            key={profile.id}
            className={`profile-chip ${selectedProfileId === profile.id ? "is-active" : ""}`}
            type="button"
            onClick={() => onSelect(profile.id)}
          >
            <strong>{profile.name}</strong>
            <span>{profile.analysis?.notes ?? profile.description ?? "Profile ready for use."}</span>
          </button>
        ))}
      </div>
    </Card>
  );
}

export function HistoryPanel({ jobs }: { jobs: ProcessingJob[] }) {
  return (
    <Card>
      <SectionTitle title="Recent Jobs" subtitle="All preview and export jobs in one stream" compact />
      <div className="history-list">
        {jobs.map((job) => (
          <article key={job.id} className="history-row">
            <div className="history-meta">
              <div>
                <p className="history-kind">{job.kind.replace("_", " ")}</p>
                <p className="muted">{formatRelativeDate(job.createdAt)}</p>
              </div>
              <Badge tone={job.status === "completed" ? "success" : job.status === "failed" ? "danger" : "warning"}>
                {formatStatus(job.status)}
              </Badge>
            </div>
            <ProgressBar value={job.progress} />
          </article>
        ))}
      </div>
    </Card>
  );
}

export function ModelStatusPanel({ health }: { health?: HealthResponse }) {
  return (
    <Card>
      <SectionTitle title="Model Manager" subtitle="Local capability check" compact />
      <div className="status-list">
        {health?.providers.map((provider) => (
          <div key={provider.id} className="status-list-row">
            <div>
              <p className="status-title">{provider.label}</p>
              <p className="muted">{provider.detail}</p>
            </div>
            <Badge tone={provider.available ? "success" : "warning"}>
              {provider.available ? "Ready" : "Optional"}
            </Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function SettingsSummary({
  settings,
}: {
  settings?: AppSettings;
}) {
  return (
    <Card>
      <SectionTitle title="Settings Snapshot" subtitle="Current local defaults" compact />
      {settings ? (
        <dl className="summary-grid">
          <div>
            <dt>Export format</dt>
            <dd>{settings.defaultExportFormat.toUpperCase()}</dd>
          </div>
          <div>
            <dt>Advanced mode</dt>
            <dd>{settings.advancedMode ? "On" : "Off"}</dd>
          </div>
          <div>
            <dt>Retention</dt>
            <dd>{settings.retentionDays} days</dd>
          </div>
          <div>
            <dt>Output folder</dt>
            <dd>{settings.defaultOutputDirectory}</dd>
          </div>
        </dl>
      ) : (
        <p className="muted">Settings are loading.</p>
      )}
    </Card>
  );
}
