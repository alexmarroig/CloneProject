import { Voice } from "../types";
import { ghost, panel } from "./styles";

type Props = {
  apiBase: string;
  voices: Voice[];
  onDeleteVoice: (voiceName: string) => Promise<void>;
};

export function VoicesPanel({ apiBase, voices, onDeleteVoice }: Props) {
  return (
    <section style={panel}>
      <div style={{ display: "grid", gap: 8 }}>
        {voices.map((voice) => (
          <div key={voice.name} style={{ border: "1px solid var(--line)", borderRadius: 10, padding: 8, display: "flex", justifyContent: "space-between", flexWrap: "wrap" }}>
            <div>
              <strong>{voice.display_name}</strong> ({voice.rvc_version})
              <br />
              <span style={{ color: "var(--muted)" }}>
                dataset: {voice.dataset_path ?? "-"} | base: {voice.base_model ?? "-"}
              </span>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <a href={`${apiBase}/voices/${encodeURIComponent(voice.name)}/download/model`} style={ghost}>
                Download model
              </a>
              <a href={`${apiBase}/voices/${encodeURIComponent(voice.name)}/download/index`} style={ghost}>
                Download index
              </a>
              <button type="button" style={{ ...ghost, borderColor: "#8b1e1e", color: "#8b1e1e" }} onClick={() => onDeleteVoice(voice.name)}>
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
