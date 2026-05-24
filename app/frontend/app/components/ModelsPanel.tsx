import { ModelInfo } from "../types";
import { ghost, inputStyle, panel, primary } from "./styles";

type Props = {
  modelDownloadUrl: string;
  models: ModelInfo[];
  onModelDownloadUrlChange: (value: string) => void;
  onDownloadModel: () => Promise<void>;
  onDeleteModel: (name: string) => Promise<void>;
};

export function ModelsPanel({ modelDownloadUrl, models, onModelDownloadUrlChange, onDownloadModel, onDeleteModel }: Props) {
  return (
    <section style={panel}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input value={modelDownloadUrl} onChange={(event) => onModelDownloadUrlChange(event.target.value)} placeholder="https://...model.pth" style={{ ...inputStyle, minWidth: 280 }} />
        <button type="button" style={primary} onClick={() => onDownloadModel()}>
          Download model
        </button>
      </div>
      <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
        {models.map((model) => (
          <div key={model.name} style={{ border: "1px solid var(--line)", borderRadius: 10, padding: 8, display: "flex", justifyContent: "space-between", flexWrap: "wrap" }}>
            <div>
              {model.name} ({model.kind})
            </div>
            <button type="button" style={{ ...ghost, borderColor: "#8b1e1e", color: "#8b1e1e" }} onClick={() => onDeleteModel(model.name)}>
              Delete
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
