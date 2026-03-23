import { useEffect, useState } from "react";
import { Button, Card, Field, Input, SectionTitle, Toggle } from "@home-voice-studio/ui";
import type { AppSettings } from "@home-voice-studio/shared-types";

interface SettingsViewProps {
  settings?: AppSettings;
  onSave(next: AppSettings): Promise<AppSettings>;
}

export function SettingsView({ settings, onSave }: SettingsViewProps) {
  const [draft, setDraft] = useState<AppSettings | undefined>(settings);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setDraft(settings);
  }, [settings]);

  if (!draft) {
    return (
      <Card>
        <SectionTitle title="Settings" subtitle="Loading local preferences..." />
      </Card>
    );
  }

  const save = async () => {
    setBusy(true);
    try {
      await onSave(draft);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="view-grid">
      <Card className="hero-card">
        <SectionTitle title="Settings" subtitle="Keep the app safe, local, and easy to use." />
        <div className="form-grid">
          <Field label="Default Export Folder">
            <Input
              value={draft.defaultOutputDirectory}
              onChange={(event) =>
                setDraft((current) =>
                  current ? { ...current, defaultOutputDirectory: event.target.value } : current,
                )
              }
            />
          </Field>

          <Field
            label="Sidecar Host"
            description="Locked to the local machine. Remote hosts are ignored."
          >
            <Input value={draft.inferenceHost} readOnly />
          </Field>

          <Field label="Advanced Controls">
            <Toggle
              checked={draft.advancedMode}
              onChange={(value) =>
                setDraft((current) => (current ? { ...current, advancedMode: value } : current))
              }
            />
          </Field>

          <Field label="Allow unsafe voice cloning">
            <Toggle
              checked={draft.allowUnsafeVoiceCloning}
              onChange={(value) =>
                setDraft((current) =>
                  current ? { ...current, allowUnsafeVoiceCloning: value } : current,
                )
              }
            />
            <p className="muted">
              Only enable this if every voice profile you use has explicit permission.
            </p>
          </Field>
        </div>
        <div className="action-row">
          <Button onClick={() => void save()} busy={busy}>
            Save Settings
          </Button>
        </div>
      </Card>
    </div>
  );
}
