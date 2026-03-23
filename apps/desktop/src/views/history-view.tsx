import { Badge, Button, Card, ProgressBar, SectionTitle } from "@home-voice-studio/ui";
import type { AppSettings, AudioArtifact, ExportRequest, OutputFormat, ProcessingJob } from "@home-voice-studio/shared-types";
import { formatRelativeDate, formatStatus } from "@/lib/format";
import { chooseExportDestination } from "@/lib/runtime";

export function HistoryView({
  jobs,
  settings,
  onExport,
}: {
  jobs: ProcessingJob[];
  settings?: AppSettings;
  onExport(request: ExportRequest): Promise<AudioArtifact>;
}) {
  return (
    <div className="view-grid">
      <Card className="hero-card">
        <SectionTitle
          title="History"
          subtitle="Track current and completed jobs, then reopen recent results."
        />
        <div className="history-list">
          {jobs.map((job) => (
            <article key={job.id} className="history-row history-row-large">
              <div className="history-meta">
                <div>
                  <p className="history-kind">{job.kind.replace("_", " ")}</p>
                  <p className="muted">
                    {formatRelativeDate(job.createdAt)} • {job.artifacts[0]?.label ?? "No artifact yet"}
                  </p>
                </div>
                <Badge tone={job.status === "completed" ? "success" : job.status === "failed" ? "danger" : "warning"}>
                  {formatStatus(job.status)}
                </Badge>
              </div>
              <ProgressBar value={job.progress} />
              {job.artifacts[0] ? (
                <div className="audio-card">
                  <audio controls preload="none" className="audio-player">
                    <source src={job.artifacts[0].path} />
                  </audio>
                  {settings ? (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() =>
                        void chooseExportDestination(
                          `${job.kind}-${Date.now()}.${job.artifacts[0].format}`,
                          settings.defaultOutputDirectory,
                        ).then((destinationPath) => {
                          if (!destinationPath) {
                            return;
                          }
                          return onExport({
                            artifactPath: job.artifacts[0].path,
                            destinationPath,
                            format: job.artifacts[0].format as OutputFormat,
                          });
                        })
                      }
                    >
                      Export Again
                    </Button>
                  ) : null}
                  <code className="path-pill">{job.artifacts[0].path}</code>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </Card>
    </div>
  );
}
