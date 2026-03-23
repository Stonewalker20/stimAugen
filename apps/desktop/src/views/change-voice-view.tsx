import { useState } from "react";
import {
  Button,
  Card,
  Field,
  Input,
  SectionTitle,
  Slider,
  Toggle,
} from "@home-voice-studio/ui";
import type {
  AppSettings,
  AudioArtifact,
  ExportRequest,
  OutputFormat,
  ProcessingJob,
  VoiceProfile,
} from "@home-voice-studio/shared-types";
import { ResultPreview } from "@/components/workspace-panels";
import { chooseAudioFile, chooseExportDestination } from "@/lib/runtime";

interface ChangeVoiceViewProps {
  profiles: VoiceProfile[];
  settings?: AppSettings;
  selectedProfileId?: string;
  onProfileChange(profileId: string): void;
  onSubmit(payload: {
    inputPath: string;
    profileId: string;
    strength: number;
    pitchPreserve: boolean;
    preview: boolean;
    outputFormat: OutputFormat;
  }): Promise<ProcessingJob>;
  onExport(request: ExportRequest): Promise<AudioArtifact>;
}

export function ChangeVoiceView({
  profiles,
  settings,
  selectedProfileId,
  onProfileChange,
  onSubmit,
  onExport,
}: ChangeVoiceViewProps) {
  const activeProfile = profiles.find((profile) => profile.id === selectedProfileId) ?? profiles[0];
  const [inputPath, setInputPath] = useState("/Users/demo/Desktop/original-voice.wav");
  const [strength, setStrength] = useState(activeProfile?.defaultSettings.strength ?? 0.65);
  const [pitchPreserve, setPitchPreserve] = useState(activeProfile?.defaultSettings.pitchPreserve ?? true);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("wav");
  const [lastJob, setLastJob] = useState<ProcessingJob>();
  const [busy, setBusy] = useState(false);
  const [exportBusy, setExportBusy] = useState(false);

  const submit = async (preview: boolean) => {
    if (!activeProfile) {
      return;
    }
    setBusy(true);
    try {
      const job = await onSubmit({
        inputPath,
        profileId: activeProfile.id,
        strength,
        pitchPreserve,
        preview,
        outputFormat,
      });
      setLastJob(job);
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
        `voice-change-${Date.now()}.${artifact.format}`,
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
          title="Change Voice"
          subtitle="Retarget recorded speech to a saved voice profile while keeping controls simple."
        />
        <div className="form-grid">
          <Field label="Input Audio">
            <div className="stack-row">
              <Input value={inputPath} onChange={(event) => setInputPath(event.target.value)} />
              <Button
                type="button"
                variant="secondary"
                onClick={() =>
                  void chooseAudioFile().then((path) => {
                    if (path) {
                      setInputPath(path);
                    }
                  })
                }
              >
                Browse
              </Button>
            </div>
          </Field>

          <Field label="Target Voice">
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

          <Field
            label={`Strength ${Math.round(strength * 100)}%`}
            description="Higher strength pushes farther toward the target voice."
          >
            <Slider min={0.15} max={1} step={0.01} value={strength} onChange={setStrength} />
          </Field>

          <Field label="Pitch Preserve" description="Keep the original melody and pitch contour.">
            <Toggle checked={pitchPreserve} onChange={setPitchPreserve} />
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
        </div>

        <div className="action-row">
          <Button onClick={() => void submit(true)} busy={busy}>
            Preview Voice Change
          </Button>
          <Button variant="secondary" onClick={() => void submit(false)} busy={busy}>
            Create Exportable File
          </Button>
        </div>
      </Card>

      <ResultPreview
        title="Before / After"
        secondaryText="Preview the most recent conversion"
        artifact={lastJob?.artifacts[0]}
        onExport={lastJob?.artifacts[0] ? () => void quickExport() : undefined}
        exportBusy={exportBusy}
      />

      <Card>
        <SectionTitle title="Conversion Notes" subtitle="Profile and source guidance" compact />
        <ul className="bullet-list">
          <li>Best results come from dry, close-mic speech with minimal reverb.</li>
          <li>Strength works best between 45% and 75% for natural output.</li>
          <li>Use Pitch Preserve when the original delivery should stay recognizable.</li>
        </ul>
      </Card>
    </div>
  );
}
