import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  Field,
  SectionTitle,
  Slider,
  TextArea,
} from "@home-voice-studio/ui";
import type { AudioArtifact, OutputFormat, ProcessingJob, VoiceProfile } from "@home-voice-studio/shared-types";
import { ResultPreview } from "@/components/workspace-panels";
import type { AppSettings, ExportRequest } from "@home-voice-studio/shared-types";
import { chooseExportDestination } from "@/lib/runtime";

interface SpeakTextViewProps {
  profiles: VoiceProfile[];
  jobs: ProcessingJob[];
  settings?: AppSettings;
  selectedProfileId?: string;
  onProfileChange(profileId: string): void;
  onSubmit(payload: {
    text: string;
    profileId: string;
    speed: number;
    preview: boolean;
    outputFormat: OutputFormat;
  }): Promise<ProcessingJob>;
  onExport(request: ExportRequest): Promise<AudioArtifact>;
}

export function SpeakTextView({
  profiles,
  jobs,
  settings,
  selectedProfileId,
  onProfileChange,
  onSubmit,
  onExport,
}: SpeakTextViewProps) {
  const activeProfile = profiles.find((profile) => profile.id === selectedProfileId) ?? profiles[0];
  const [text, setText] = useState(
    "Welcome home. Your dinner timer is running, and the front porch package has arrived.",
  );
  const [speed, setSpeed] = useState(activeProfile?.defaultSettings.speed ?? 1);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("wav");
  const [lastJobId, setLastJobId] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [exportBusy, setExportBusy] = useState(false);
  const lastJob = useMemo(() => jobs.find((job) => job.id === lastJobId), [jobs, lastJobId]);

  useEffect(() => {
    setSpeed(activeProfile?.defaultSettings.speed ?? 1);
  }, [activeProfile?.id, activeProfile?.defaultSettings.speed]);

  const submit = async (preview: boolean) => {
    if (!activeProfile) {
      return;
    }
    setBusy(true);
    try {
      const job = await onSubmit({
        text,
        profileId: activeProfile.id,
        speed,
        preview,
        outputFormat,
      });
      setLastJobId(job.id);
    } finally {
      setBusy(false);
    }
  };

  const quickExport = async () => {
    const artifact = lastJob?.artifacts[0];
    if (!artifact || !settings) {
      return;
    }
    setExportBusy(true);
    try {
      const destinationPath = await chooseExportDestination(
        `speech-${Date.now()}.${artifact.format}`,
        settings.defaultOutputDirectory,
      );
      if (!destinationPath) {
        return;
      }
      await onExport({
        artifactPath: artifact.path,
        destinationPath,
        format: artifact.format as OutputFormat,
      });
    } finally {
      setExportBusy(false);
    }
  };

  return (
    <div className="view-grid">
      <Card className="hero-card">
        <SectionTitle
          title="Speak Text"
          subtitle="Type what you want to say, pick a saved voice, and generate speech locally."
        />
        <div className="form-grid">
          <Field label="Voice">
            <select
              className="ui-input"
              value={activeProfile?.id}
              onChange={(event) => onProfileChange(event.target.value)}
            >
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Output Format">
            <div className="segmented-control">
              {(["wav", "mp3"] as OutputFormat[]).map((format) => (
                <button
                  key={format}
                  type="button"
                  className={outputFormat === format ? "is-active" : ""}
                  onClick={() => setOutputFormat(format)}
                >
                  {format.toUpperCase()}
                </button>
              ))}
            </div>
          </Field>

          <Field
            label={`Speed ${speed.toFixed(2)}x`}
            description="Keep it simple. Higher values speak faster."
          >
            <Slider
              min={0.7}
              max={1.35}
              step={0.01}
              value={speed}
              onChange={setSpeed}
            />
          </Field>

          <Field label="Text">
            <TextArea value={text} onChange={(event) => setText(event.target.value)} rows={8} />
          </Field>
        </div>

        <div className="action-row">
          <Button onClick={() => void submit(true)} busy={busy}>
            Generate Preview
          </Button>
          <Button variant="secondary" onClick={() => void submit(false)} busy={busy}>
            Create Exportable File
          </Button>
        </div>
      </Card>

      <ResultPreview
        title="Speech Preview"
        secondaryText="Latest generated clip"
        artifact={lastJob?.artifacts[0]}
        onExport={lastJob?.artifacts[0] ? () => void quickExport() : undefined}
        exportBusy={exportBusy}
      />

      <Card>
        <SectionTitle title="Selected Voice" subtitle="Quick profile details" compact />
        {activeProfile ? (
          <div className="details-grid">
            <div>
              <p className="detail-label">Name</p>
              <p>{activeProfile.name}</p>
            </div>
            <div>
              <p className="detail-label">Consent</p>
              <p>{activeProfile.consentConfirmed ? "Confirmed" : "Missing"}</p>
            </div>
            <div>
              <p className="detail-label">Profile notes</p>
              <p>{activeProfile.analysis?.notes ?? activeProfile.description ?? "No notes yet."}</p>
            </div>
            <div>
              <p className="detail-label">Reference clips</p>
              <p>{activeProfile.referenceClips.length}</p>
            </div>
          </div>
        ) : (
          <p className="muted">Create a profile first to generate speech.</p>
        )}
      </Card>
    </div>
  );
}
