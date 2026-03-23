import { useState } from "react";
import { Button, Card, SectionTitle, Spinner } from "@home-voice-studio/ui";
import {
  AppShell,
  secondaryViews,
  type MainView,
  type SecondaryView,
} from "@/components/app-shell";
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
  const [libraryOpen, setLibraryOpen] = useState(false);

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
            onCreateProfile={createProfile}
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
      libraryOpen={libraryOpen}
      onMainViewChange={setActiveMainView}
      onLibraryToggle={() => setLibraryOpen((current) => !current)}
      onRefresh={() => void refresh()}
      refreshing={state.refreshing}
    >
      <div className="workspace-stack">
        <section className="workspace-primary">{mainView}</section>

        {libraryOpen ? (
          <Card className="library-drawer">
            <div className="library-header">
              <SectionTitle
                title="Library"
                subtitle="Profiles, history, settings, and model status are tucked away here."
              />
              <Button variant="secondary" size="sm" onClick={() => setLibraryOpen(false)}>
                Hide library
              </Button>
            </div>

            <div className="secondary-nav library-nav">
              {secondaryViews.map((view) => (
                <button
                  key={view.id}
                  className={`secondary-chip ${activeSecondaryView === view.id ? "is-active" : ""}`}
                  type="button"
                  onClick={() => {
                    setActiveSecondaryView(view.id);
                    setLibraryOpen(true);
                  }}
                >
                  {view.label}
                </button>
              ))}
            </div>

            {secondaryView}
          </Card>
        ) : null}
      </div>
    </AppShell>
  );
}
