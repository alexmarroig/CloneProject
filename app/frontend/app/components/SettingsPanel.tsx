import { Health, RuntimeSettings } from "../types";
import { inputStyle, panel, primary } from "./styles";

type Props = {
  apiBase: string;
  health: Health | null;
  settings: RuntimeSettings;
  onChange: (next: RuntimeSettings) => void;
  onSave: () => Promise<void>;
};

export function SettingsPanel({ apiBase, health, settings, onChange, onSave }: Props) {
  return (
    <section style={panel}>
      <div>API: {apiBase}</div>
      <div>default device: {health?.device}</div>
      <div>ffmpeg: {String(health?.ffmpeg_available)}</div>
      <div>xtts env: {String(health?.xtts_env_available)}</div>
      <div>rvc env: {String(health?.rvc_env_available)}</div>
      <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input
          value={settings.default_xtts_model ?? ""}
          onChange={(event) => onChange({ ...settings, default_xtts_model: event.target.value })}
          placeholder="default xtts model"
          style={{ ...inputStyle, minWidth: 280 }}
        />
        <input
          value={settings.default_rvc_model ?? ""}
          onChange={(event) => onChange({ ...settings, default_rvc_model: event.target.value })}
          placeholder="default rvc model"
          style={{ ...inputStyle, minWidth: 280 }}
        />
        <button type="button" style={primary} onClick={() => onSave()}>
          Save settings
        </button>
      </div>
    </section>
  );
}
