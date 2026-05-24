import { Job, JobEvent, JobLogs } from "../types";
import { ghost, panel } from "./styles";

type Props = {
  jobs: Job[];
  jobLogs: JobLogs | null;
  liveEvents: JobEvent[];
  streamingJobId: string | null;
  onFetchLogs: (jobId: string) => Promise<void>;
  onToggleStream: (jobId: string) => void;
};

export function JobsPanel({ jobs, jobLogs, liveEvents, streamingJobId, onFetchLogs, onToggleStream }: Props) {
  return (
    <section style={{ ...panel, display: "grid", gap: 8 }}>
      {jobs.map((job) => (
        <article key={job.id} style={{ border: "1px solid var(--line)", borderRadius: 12, padding: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap" }}>
            <strong>{job.type}</strong>
            <span>{job.status}</span>
          </div>
          <div style={{ color: "var(--muted)" }}>{job.phase}</div>
          <div style={{ height: 8, background: "#eadfce", borderRadius: 999, marginTop: 8, overflow: "hidden" }}>
            <div style={{ width: `${job.progress}%`, height: "100%", background: "linear-gradient(90deg, var(--accent), #265978)" }} />
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
            <button type="button" style={ghost} onClick={() => onFetchLogs(job.id)}>
              Training logs
            </button>
            <button type="button" style={ghost} onClick={() => onToggleStream(job.id)}>
              {streamingJobId === job.id ? "Stop stream" : "Live stream"}
            </button>
          </div>
          {job.error ? <div style={{ color: "#8b1e1e", marginTop: 8 }}>{job.error}</div> : null}
        </article>
      ))}
      {jobLogs ? <pre style={{ background: "#f8f0e2", border: "1px solid var(--line)", borderRadius: 10, padding: 10, maxHeight: 240, overflow: "auto" }}>{JSON.stringify(jobLogs, null, 2)}</pre> : null}
      {liveEvents.length ? (
        <pre style={{ background: "#f8f0e2", border: "1px solid var(--line)", borderRadius: 10, padding: 10, maxHeight: 260, overflow: "auto" }}>
          {JSON.stringify(liveEvents, null, 2)}
        </pre>
      ) : null}
    </section>
  );
}
