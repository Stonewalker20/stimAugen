import { useMemo, useState } from "react";
import {
  Button,
  Card,
  Field,
  Input,
  SectionTitle,
  Slider,
} from "@home-voice-studio/ui";
import type {
  AppSettings,
  AudioArtifact,
  CleanupMode,
  ExportRequest,
  OutputFormat,
  ProcessingJob,
} from "@home-voice-studio/shared-types";
import { cleanupModeLabels } from "@/lib/mock-data";
import { ResultPreview } from "@/components/workspace-panels";
import { chooseAudioFile, chooseExportDestination } from "@/lib/runtime";

interface CleanRecordingViewProps {
  jobs: ProcessingJob[];
  settings?: AppSettings;
  onSubmit(payload: {
    inputPath: string;
    mode: CleanupMode;
    cleanupLevel: number;
    preview: boolean;
    outputFormat: OutputFormat;
  }): Promise<ProcessingJob>;
  onExport(request: ExportRequest): Promise<AudioArtifact>;
}

export function CleanRecordingView({ jobs, onSubmit, onExport, settings }: CleanRecordingViewProps) {
  const [inputPath, setInputPath] = useState("/Users/demo/Desktop/noisy-porch-message.wav");
  const [mode, setMode] = useState<CleanupMode>("voice_focus");
  const [cleanupLevel, setCleanupLevel] = useState(0.58);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("wav");
  const [lastJobId, setLastJobId] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [exportBusy, setExportBusy] = useState(false);
  const lastJob = useMemo(() => jobs.find((job) => job.id === lastJobId), [jobs, lastJobId]);

  const submit = async (preview: boolean) => {
    setBusy(true);
    try {
      const job = await onSubmit({
        inputPath,
        mode,
        cleanupLevel,
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
        `cleanup-${Date.now()}.${artifact.format}`,
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
          title="Clean Recording"
          subtitle="Clean noisy recordings before export or before you retarget them to another voice."
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

          <Field label="Cleanup Mode">
            <div className="mode-grid">
              {(Object.keys(cleanupModeLabels) as CleanupMode[]).map((key) => (
                <button
                  key={key}
                  type="button"
                  className={`mode-card ${mode === key ? "is-active" : ""}`}
                  onClick={() => setMode(key)}
                >
                  <strong>{cleanupModeLabels[key]}</strong>
                  <span>
                    {key === "denoise"
                      ? "Reduce steady room or fan noise."
                      : key === "voice_focus"
                        ? "Bring speech forward for everyday recordings."
                        : "Lift vocals away from music or ambience."}
                  </span>
                </button>
              ))}
            </div>
          </Field>

          <Field
            label={`Cleanup Level ${Math.round(cleanupLevel * 100)}%`}
            description="Start in the middle and raise only if the room noise is persistent."
          >
            <Slider
              min={0.15}
              max={1}
              step={0.01}
              value={cleanupLevel}
              onChange={setCleanupLevel}
            />
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
            Preview Cleanup
          </Button>
          <Button variant="secondary" onClick={() => void submit(false)} busy={busy}>
            Create Exportable File
          </Button>
        </div>
        <p className="muted">Use this before Change Voice when the original track is too noisy to work with directly.</p>
      </Card>

      <ResultPreview
        title="Cleaned Preview"
        secondaryText="Latest restored clip"
        job={lastJob}
        artifact={lastJob?.artifacts[0]}
        onExport={lastJob?.artifacts[0] ? () => void quickExport() : undefined}
        exportBusy={exportBusy}
      />

      <Card>
        <SectionTitle title="Best Starting Point" subtitle="Plain-language guidance" compact />
        <ul className="bullet-list">
          <li>Denoise is best for fans, air conditioners, and low room hum.</li>
          <li>Voice Focus works well for phone recordings and casual room capture.</li>
          <li>Vocal Isolation is strongest for song lines or speech mixed with music.</li>
        </ul>
      </Card>
    </div>
  );
}
