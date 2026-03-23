import type { ReactNode } from "react";
import {
  Badge,
  Button,
  Card,
  SectionTitle,
} from "@home-voice-studio/ui";
import type { HealthResponse } from "@home-voice-studio/shared-types";

export type MainView = "speak" | "convert" | "clean";
export type SecondaryView = "profiles" | "history" | "settings" | "models";

const mainTabs: { id: MainView; label: string; caption: string }[] = [
  { id: "speak", label: "Speak Text", caption: "Generate speech from typed words." },
  { id: "convert", label: "Change Voice", caption: "Retarget recorded speech." },
  { id: "clean", label: "Clean Recording", caption: "Reduce noise and sharpen speech." },
];

export const secondaryViews: { id: SecondaryView; label: string }[] = [
  { id: "profiles", label: "Voice Profiles" },
  { id: "history", label: "History" },
  { id: "settings", label: "Settings" },
  { id: "models", label: "Model Manager" },
];

interface AppShellProps {
  children: ReactNode;
  health?: HealthResponse;
  activeMainView: MainView;
  libraryOpen: boolean;
  onMainViewChange(next: MainView): void;
  onLibraryToggle(): void;
  onRefresh(): void;
  refreshing: boolean;
}

export function AppShell({
  children,
  health,
  activeMainView,
  libraryOpen,
  onMainViewChange,
  onLibraryToggle,
  onRefresh,
  refreshing,
}: AppShellProps) {
  const requiredUnavailableProviders =
    health?.providers.filter((provider) => provider.required !== false && !provider.available) ?? [];
  const isDegraded = health?.status === "degraded" || requiredUnavailableProviders.length > 0;

  return (
    <div className="app-shell">
      <aside className="left-rail">
        <div className="brand-lockup">
          <p className="eyebrow">Home Voice Studio</p>
          <h1>Speak Text first. Keep the rest nearby.</h1>
          <p className="muted">
            Start with speech generation, then open the library only when you need profiles,
            history, settings, or model status.
          </p>
        </div>

        <nav className="nav-stack">
          <SectionTitle
            title="Primary Workflows"
            subtitle="Start from what you want to do."
          />
          {mainTabs.map((tab) => (
            <button
              key={tab.id}
              className={`nav-card ${activeMainView === tab.id ? "is-active" : ""}`}
              type="button"
              onClick={() => onMainViewChange(tab.id)}
            >
              <span>{tab.label}</span>
              <small>{tab.caption}</small>
            </button>
          ))}
        </nav>

        <Card className="library-card">
          <SectionTitle
            title="Library"
            subtitle="Profiles, history, settings, and model status stay out of the way."
            compact
          />
          <p className="muted library-copy">
            {libraryOpen
              ? "The library drawer is open in the main workspace."
              : "Open it when you want to manage saved voices or inspect past jobs."}
          </p>
          <Button variant="secondary" size="sm" onClick={onLibraryToggle}>
            {libraryOpen ? "Hide library" : "Open library"}
          </Button>
        </Card>

        <Card className="status-card">
          <div className="status-row">
            <SectionTitle title="Sidecar Status" subtitle="Local engine availability" compact />
            <Badge tone={isDegraded ? "warning" : "success"}>
              {isDegraded ? "Needs attention" : "Healthy"}
            </Badge>
          </div>
          <p className="muted">
            {requiredUnavailableProviders[0]?.detail ??
              "All core providers are available."}
          </p>
          <Button variant="secondary" size="sm" onClick={onRefresh} busy={refreshing}>
            Refresh status
          </Button>
        </Card>
      </aside>

      <main className="workspace">
        {isDegraded ? (
          <Card className="status-banner">
            <div className="status-row">
              <div>
                <SectionTitle
                  title="Local engine attention needed"
                  subtitle="One or more offline providers are unavailable. You can keep browsing, then refresh after starting the sidecar."
                  compact
                />
                <p className="muted">
                  {requiredUnavailableProviders.length > 0
                    ? requiredUnavailableProviders.map((provider) => provider.label).join(", ")
                    : "The sidecar reported a degraded local state."}
                </p>
              </div>
              <Button variant="secondary" size="sm" onClick={onRefresh} busy={refreshing}>
                Retry health check
              </Button>
            </div>
          </Card>
        ) : null}
        {children}
      </main>
    </div>
  );
}
