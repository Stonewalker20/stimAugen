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
  { id: "speak", label: "Speak Text", caption: "Turn typed words into voice." },
  { id: "convert", label: "Change Voice", caption: "Retarget recorded speech." },
  { id: "clean", label: "Clean Recording", caption: "Remove noise and focus speech." },
];

const secondaryViews: { id: SecondaryView; label: string }[] = [
  { id: "profiles", label: "Voice Profiles" },
  { id: "history", label: "History" },
  { id: "settings", label: "Settings" },
  { id: "models", label: "Model Manager" },
];

interface AppShellProps {
  children: ReactNode;
  health?: HealthResponse;
  activeMainView: MainView;
  activeSecondaryView: SecondaryView;
  onMainViewChange(next: MainView): void;
  onSecondaryViewChange(next: SecondaryView): void;
  onRefresh(): void;
  refreshing: boolean;
}

export function AppShell({
  children,
  health,
  activeMainView,
  activeSecondaryView,
  onMainViewChange,
  onSecondaryViewChange,
  onRefresh,
  refreshing,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="left-rail">
        <div className="brand-lockup">
          <p className="eyebrow">Home Voice Studio</p>
          <h1>Local voice tools for the house.</h1>
          <p className="muted">
            Build speech, reshape voice, and clean recordings without leaving your desktop.
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

        <nav className="nav-stack">
          <SectionTitle
            title="Library"
            subtitle="Profiles, jobs, settings, and model health."
          />
          <div className="secondary-nav">
            {secondaryViews.map((view) => (
              <button
                key={view.id}
                className={`secondary-chip ${activeSecondaryView === view.id ? "is-active" : ""}`}
                type="button"
                onClick={() => onSecondaryViewChange(view.id)}
              >
                {view.label}
              </button>
            ))}
          </div>
        </nav>

        <Card className="status-card">
          <div className="status-row">
            <SectionTitle title="Sidecar Status" subtitle="Local engine availability" compact />
            <Badge tone={health?.status === "ok" ? "success" : "warning"}>
              {health?.status === "ok" ? "Healthy" : "Needs attention"}
            </Badge>
          </div>
          <p className="muted">
            {health?.providers.find((provider) => !provider.available)?.detail ??
              "All core providers are available."}
          </p>
          <Button variant="secondary" size="sm" onClick={onRefresh} busy={refreshing}>
            Refresh status
          </Button>
        </Card>
      </aside>

      <main className="workspace">{children}</main>
    </div>
  );
}
