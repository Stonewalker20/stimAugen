import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Button,
  Card,
  Field,
  Input,
  SectionTitle,
  Slider,
  Toggle,
  TextArea,
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
import { chooseAudioFile, chooseAudioFiles, chooseExportDestination } from "@/lib/runtime";

const isBuiltInVoiceId = (profileId: string) => profileId.startsWith("sample_") || profileId.startsWith("sample-");

interface ChangeVoiceViewProps {
  profiles: VoiceProfile[];
  jobs: ProcessingJob[];
  settings?: AppSettings;
  selectedProfileId?: string;
  onProfileChange(profileId: string): void;
  onCreateProfile(payload: {
    name: string;
    description?: string;
    consentConfirmed: boolean;
    referenceClipPaths: string[];
  }): Promise<VoiceProfile>;
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
  jobs,
  settings,
  selectedProfileId,
  onProfileChange,
  onCreateProfile,
  onSubmit,
  onExport,
}: ChangeVoiceViewProps) {
  const activeProfile = profiles.find((profile) => profile.id === selectedProfileId) ?? profiles[0];
  const featuredProfiles = useMemo(() => {
    const starterVoices = profiles.filter((profile) => isBuiltInVoiceId(profile.id));
    if (starterVoices.length > 0) {
      return starterVoices;
    }
    return profiles.slice(0, Math.min(3, profiles.length));
  }, [profiles]);
  const consentBlocked = Boolean(activeProfile && !activeProfile.consentConfirmed && !settings?.allowUnsafeVoiceCloning);
  const [inputPath, setInputPath] = useState("/Users/demo/Desktop/original-voice.wav");
  const [strength, setStrength] = useState(activeProfile?.defaultSettings.strength ?? 0.65);
  const [pitchPreserve, setPitchPreserve] = useState(activeProfile?.defaultSettings.pitchPreserve ?? true);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("wav");
  const [lastJobId, setLastJobId] = useState<string>();
  const [busy, setBusy] = useState(false);
  const [exportBusy, setExportBusy] = useState(false);
  const [voiceName, setVoiceName] = useState("");
  const [voiceDescription, setVoiceDescription] = useState("");
  const [referenceClipPaths, setReferenceClipPaths] = useState(
    "/Users/demo/Desktop/my-voice-reference-1.wav\n/Users/demo/Desktop/my-voice-reference-2.wav",
  );
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [creatingVoice, setCreatingVoice] = useState(false);
  const lastJob = useMemo(() => jobs.find((job) => job.id === lastJobId), [jobs, lastJobId]);

  useEffect(() => {
    setStrength(activeProfile?.defaultSettings.strength ?? 0.65);
    setPitchPreserve(activeProfile?.defaultSettings.pitchPreserve ?? true);
  }, [
    activeProfile?.id,
    activeProfile?.defaultSettings.strength,
    activeProfile?.defaultSettings.pitchPreserve,
  ]);

  const submit = async (preview: boolean) => {
    if (!activeProfile) {
      return;
    }
    if (consentBlocked) {
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

  const createMyVoice = async () => {
    const trimmedName = voiceName.trim();
    const clipPaths = referenceClipPaths
      .split("\n")
      .map((value) => value.trim())
      .filter(Boolean);
    if (!trimmedName || !consentConfirmed || clipPaths.length === 0) {
      return;
    }
    setCreatingVoice(true);
    try {
      await onCreateProfile({
        name: trimmedName,
        description: voiceDescription.trim() || undefined,
        consentConfirmed,
        referenceClipPaths: clipPaths,
      });
      setVoiceName("");
      setVoiceDescription("");
      setReferenceClipPaths("");
      setConsentConfirmed(false);
    } finally {
      setCreatingVoice(false);
    }
  };

  return (
    <div className="view-grid">
      <Card className="hero-card">
        <SectionTitle
          title="Change Voice"
          subtitle="Retarget recorded speech to a saved voice profile while keeping controls simple."
        />
        <SectionTitle title="Default Voices" subtitle="Pick a built-in voice or switch to one you created." compact />
        <div className="profile-strip">
          {featuredProfiles.map((profile) => (
            <button
              key={profile.id}
              type="button"
              className={`profile-chip ${activeProfile?.id === profile.id ? "is-active" : ""}`}
              onClick={() => onProfileChange(profile.id)}
            >
              <strong>{profile.name}</strong>
              <span>{profile.description ?? "Ready to use."}</span>
              <Badge tone={isBuiltInVoiceId(profile.id) ? "success" : "neutral"}>
                {isBuiltInVoiceId(profile.id) ? "Built-in" : "Saved"}
              </Badge>
            </button>
          ))}
        </div>
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
          <Button onClick={() => void submit(true)} busy={busy} disabled={!activeProfile || consentBlocked}>
            Preview Voice Change
          </Button>
          <Button
            variant="secondary"
            onClick={() => void submit(false)}
            busy={busy}
            disabled={!activeProfile || consentBlocked}
          >
            Create Exportable File
          </Button>
        </div>
        {consentBlocked ? (
          <p className="muted">
            Voice conversion is locked until this profile has explicit consent, or unsafe cloning is enabled in Settings.
          </p>
        ) : null}
      </Card>

      <Card>
        <SectionTitle
          title="Create Your Own Voice"
          subtitle="Upload one or more clips, confirm permission, and save a voice you can reuse in speech or conversion."
        />
        <div className="form-grid">
          <Field label="Voice Name">
            <Input value={voiceName} onChange={(event) => setVoiceName(event.target.value)} />
          </Field>

          <Field label="Description">
            <TextArea
              value={voiceDescription}
              onChange={(event) => setVoiceDescription(event.target.value)}
              rows={3}
            />
          </Field>

          <Field label="Reference Audio" description="One local audio file path per line.">
            <>
              <TextArea
                value={referenceClipPaths}
                onChange={(event) => setReferenceClipPaths(event.target.value)}
                rows={4}
              />
              <div className="action-row">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() =>
                    void chooseAudioFiles().then((paths) => {
                      if (paths.length) {
                        setReferenceClipPaths(paths.join("\n"));
                      }
                    })
                  }
                >
                  Choose Audio Files
                </Button>
              </div>
            </>
          </Field>

          <Field
            label="Voice cloning consent"
            description="Required before a voice profile can be saved or used in conversion."
          >
            <Toggle checked={consentConfirmed} onChange={setConsentConfirmed} />
          </Field>
        </div>

        <div className="action-row">
          <Button onClick={() => void createMyVoice()} busy={creatingVoice}>
            Create Voice From Uploads
          </Button>
        </div>
      </Card>

      <ResultPreview
        title="Before / After"
        secondaryText="Preview the most recent conversion"
        job={lastJob}
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
