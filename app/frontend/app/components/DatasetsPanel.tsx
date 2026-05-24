import { DatasetDetails, DatasetSummary } from "../types";
import { ghost, inputStyle, panel, primary } from "./styles";

type Props = {
  datasets: DatasetSummary[];
  datasetDetails: DatasetDetails | null;
  datasetUploadName: string;
  datasetUploadFile: File | null;
  onDatasetUploadNameChange: (value: string) => void;
  onDatasetUploadFileChange: (file: File | null) => void;
  onUploadDataset: () => Promise<void>;
  onPreviewDataset: (name: string) => Promise<void>;
};

export function DatasetsPanel({
  datasets,
  datasetDetails,
  datasetUploadName,
  datasetUploadFile,
  onDatasetUploadNameChange,
  onDatasetUploadFileChange,
  onUploadDataset,
  onPreviewDataset,
}: Props) {
  return (
    <section style={panel}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input value={datasetUploadName} onChange={(event) => onDatasetUploadNameChange(event.target.value)} placeholder="dataset name" style={{ ...inputStyle, maxWidth: 220 }} />
        <input type="file" accept="audio/*" onChange={(event) => onDatasetUploadFileChange(event.target.files?.[0] ?? null)} style={{ ...inputStyle, maxWidth: 260 }} />
        <button type="button" style={primary} onClick={() => onUploadDataset()} disabled={!datasetUploadFile}>
          Upload dataset
        </button>
      </div>
      <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
        {datasets.map((dataset) => (
          <div key={dataset.name} style={{ border: "1px solid var(--line)", borderRadius: 10, padding: 8, display: "flex", justifyContent: "space-between", flexWrap: "wrap" }}>
            <div>
              {dataset.name} | {dataset.file_count} files | {dataset.total_duration_seconds.toFixed(2)}s
            </div>
            <button type="button" style={ghost} onClick={() => onPreviewDataset(dataset.name)}>
              Preview
            </button>
          </div>
        ))}
      </div>
      {datasetDetails ? <pre style={{ marginTop: 10, maxHeight: 180, overflow: "auto", background: "#f8f0e2", padding: 10 }}>{JSON.stringify(datasetDetails, null, 2)}</pre> : null}
    </section>
  );
}
