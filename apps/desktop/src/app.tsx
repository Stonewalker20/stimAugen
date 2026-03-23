import { useState } from "react";
import { Button, Card, Spinner } from "@home-voice-studio/ui";
import { AppShell, type MainView, type SecondaryView } from "@/components/app-shell";
import {
  HistoryPanel,
  ModelStatusPanel,
  ProfileStrip,
  SettingsSummary,
} from "@/components/workspace-panels";
import { useWorkspaceState } from "@/lib/state";
import { CleanRecordingView } from "@/views/clean-recording-view";
import { ChangeVoiceView } from "@/views/change-voice-view";
import { HistoryView } from "@/views/history-view";
import { ModelManagerView } from "@/views/model-manager-view";
import { SettingsView } from "@/views/settings-view";
import { SpeakTextView } from "@/views/speak-text-view";
import { VoiceProfilesView } from "@/views/voice-profiles-view";

export function App() {
  const {
    state,
    refresh,
    createProfile,
    submitTts,
    submitVoiceConversion,
    submitIsolation,
    saveSettings,
    exportArtifact,
    setSelectedProfileId,
  } = useWorkspaceState();
  const [activeMainView, setActiveMainView] = useState<MainView>("speak");
  const [activeSecondaryView, setActiveSecondaryView] = useState<SecondaryView>("profiles");

  if (state.loading) {
    return (
      <div className="loading-screen">
        <Spinner />
        <p>Loading Home Voice Studio…</p>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="loading-screen">
        <Card>
          <p>{state.error}</p>
          <Button onClick={() => void refresh()}>Retry</Button>
        </Card>
      </div>
    );
  }

  const mainView = (() => {
    switch (activeMainView) {
      case "speak":
        return (
          <SpeakTextView
            profiles={state.profiles}
            jobs={state.jobs}
            settings={state.settings}
            selectedProfileId={state.selectedProfileId}
            onProfileChange={setSelectedProfileId}
            onSubmit={submitTts}
            onExport={exportArtifact}
          />
        );
      case "convert":
        return (
          <ChangeVoiceView
            profiles={state.profiles}
            jobs={state.jobs}
            settings={state.settings}
            selectedProfileId={state.selectedProfileId}
            onProfileChange={setSelectedProfileId}
            onSubmit={submitVoiceConversion}
            onExport={exportArtifact}
          />
        );
      case "clean":
        return (
          <CleanRecordingView
            jobs={state.jobs}
            settings={state.settings}
            onSubmit={submitIsolation}
            onExport={exportArtifact}
          />
        );
    }
  })();

  const secondaryView = (() => {
    switch (activeSecondaryView) {
      case "profiles":
        return <VoiceProfilesView profiles={state.profiles} onCreateProfile={createProfile} />;
      case "history":
        return <HistoryView jobs={state.jobs} settings={state.settings} onExport={exportArtifact} />;
      case "settings":
        return <SettingsView settings={state.settings} onSave={saveSettings} />;
      case "models":
        return <ModelManagerView health={state.health} />;
    }
  })();

  return (
    <AppShell
      health={state.health}
      activeMainView={activeMainView}
      activeSecondaryView={activeSecondaryView}
      onMainViewChange={setActiveMainView}
      onSecondaryViewChange={setActiveSecondaryView}
      onRefresh={() => void refresh()}
      refreshing={state.refreshing}
    >
      <div className="workspace-grid">
        <section className="workspace-primary">
          <ProfileStrip
            profiles={state.profiles}
            selectedProfileId={state.selectedProfileId}
            onSelect={setSelectedProfileId}
          />
          {mainView}
        </section>

        <aside className="workspace-secondary">
          <HistoryPanel jobs={state.jobs} />
          <ModelStatusPanel health={state.health} />
          <SettingsSummary settings={state.settings} />
          {secondaryView}
        </aside>
      </div>
    </AppShell>
  );
}
