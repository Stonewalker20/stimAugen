import { useState } from "react";
import {
  Badge,
  Button,
  Card,
  Field,
  Input,
  SectionTitle,
  TextArea,
  Toggle,
} from "@home-voice-studio/ui";
import type { VoiceProfile } from "@home-voice-studio/shared-types";
import { formatRelativeDate } from "@/lib/format";
import { chooseAudioFiles } from "@/lib/runtime";

interface VoiceProfilesViewProps {
  profiles: VoiceProfile[];
  onCreateProfile(payload: {
    name: string;
    description?: string;
    consentConfirmed: boolean;
    referenceClipPaths: string[];
  }): Promise<VoiceProfile>;
}

export function VoiceProfilesView({
  profiles,
  onCreateProfile,
}: VoiceProfilesViewProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [clipPaths, setClipPaths] = useState(
    "/Users/demo/Desktop/reference-1.wav\n/Users/demo/Desktop/reference-2.wav",
  );
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!name || !consentConfirmed) {
      return;
    }
    setBusy(true);
    try {
      await onCreateProfile({
        name,
        description,
        consentConfirmed,
        referenceClipPaths: clipPaths
          .split("\n")
          .map((value) => value.trim())
          .filter(Boolean),
      });
      setName("");
      setDescription("");
      setClipPaths("");
      setConsentConfirmed(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="view-grid">
      <Card className="hero-card">
        <SectionTitle
          title="Voice Profiles"
          subtitle="Save reusable target voices with explicit consent and clear reference management."
        />
        <div className="form-grid">
          <Field label="Profile Name">
            <Input value={name} onChange={(event) => setName(event.target.value)} />
          </Field>

          <Field label="Description">
            <TextArea value={description} onChange={(event) => setDescription(event.target.value)} rows={4} />
          </Field>

          <Field label="Reference Clip Paths" description="One local file path per line.">
            <>
              <TextArea value={clipPaths} onChange={(event) => setClipPaths(event.target.value)} rows={5} />
              <div className="action-row">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() =>
                    void chooseAudioFiles().then((paths) => {
                      if (paths.length) {
                        setClipPaths(paths.join("\n"));
                      }
                    })
                  }
                >
                  Choose Reference Clips
                </Button>
              </div>
            </>
          </Field>

          <Field
            label="Voice cloning consent"
            description="Required before a profile can be created or used for conversion."
          >
            <Toggle checked={consentConfirmed} onChange={setConsentConfirmed} />
          </Field>
        </div>

        <div className="action-row">
          <Button onClick={() => void submit()} busy={busy}>
            Create Voice Profile
          </Button>
        </div>
      </Card>

      <Card>
        <SectionTitle title="Saved Profiles" subtitle="Available across TTS and voice change" compact />
        <div className="profile-list">
          {profiles.map((profile) => (
            <article key={profile.id} className="profile-list-row">
              <div className="profile-list-head">
                <div>
                  <p className="profile-name">{profile.name}</p>
                  <p className="muted">{profile.description ?? "No description added."}</p>
                </div>
                <Badge tone={profile.embeddingStatus === "ready" ? "success" : "warning"}>
                  {profile.embeddingStatus.replace("_", " ")}
                </Badge>
              </div>
              <div className="details-grid">
                <div>
                  <p className="detail-label">Created</p>
                  <p>{formatRelativeDate(profile.createdAt)}</p>
                </div>
                <div>
                  <p className="detail-label">Reference clips</p>
                  <p>{profile.referenceClips.length}</p>
                </div>
                <div>
                  <p className="detail-label">Consent</p>
                  <p>{profile.consentConfirmed ? "Confirmed" : "Missing"}</p>
                </div>
                <div>
                  <p className="detail-label">Notes</p>
                  <p>{profile.analysis?.notes ?? "Profile analysis pending."}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </Card>
    </div>
  );
}
