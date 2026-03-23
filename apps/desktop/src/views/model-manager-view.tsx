import { Badge, Card, SectionTitle } from "@home-voice-studio/ui";
import type { HealthResponse } from "@home-voice-studio/shared-types";

export function ModelManagerView({ health }: { health?: HealthResponse }) {
  return (
    <div className="view-grid">
      <Card className="hero-card">
        <SectionTitle
          title="Model Manager"
          subtitle="Check which local engines are ready and what improves when optional tools are installed."
        />
        <div className="status-list">
          {health?.providers.map((provider) => (
            <article key={provider.id} className="status-list-row status-list-row-large">
              <div>
                <p className="status-title">{provider.label}</p>
                <p className="muted">{provider.detail}</p>
              </div>
              <Badge tone={provider.available ? "success" : "warning"}>
                {provider.available ? "Available" : "Optional"}
              </Badge>
            </article>
          ))}
        </div>
      </Card>
    </div>
  );
}
