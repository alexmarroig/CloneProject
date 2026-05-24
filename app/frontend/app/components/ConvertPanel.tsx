import { FormEvent } from "react";

import { ConvertForm, Voice } from "../types";
import { ghost, inputStyle, panel, primary } from "./styles";

type Props = {
  form: ConvertForm;
  voices: Voice[];
  audioUploadFile: File | null;
  onAudioUploadFileChange: (file: File | null) => void;
  onChange: (next: ConvertForm) => void;
  onUploadAudio: () => Promise<void>;
  onSubmit: (event: FormEvent) => void;
};

export function ConvertPanel({ form, voices, audioUploadFile, onAudioUploadFileChange, onChange, onUploadAudio, onSubmit }: Props) {
  return (
    <form onSubmit={onSubmit} style={panel}>
      <h2 style={{ marginTop: 0 }}>Convert</h2>
      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))" }}>
        <input type="file" accept="audio/*" onChange={(event) => onAudioUploadFileChange(event.target.files?.[0] ?? null)} style={inputStyle} />
        <button type="button" style={ghost} onClick={() => onUploadAudio()} disabled={!audioUploadFile}>
          Upload input audio
        </button>
        <input value={form.input_path} onChange={(event) => onChange({ ...form, input_path: event.target.value })} placeholder="input path" style={inputStyle} />
        <select value={form.voice} onChange={(event) => onChange({ ...form, voice: event.target.value })} style={inputStyle}>
          <option value="">voice or explicit paths</option>
          {voices.map((voice) => (
            <option key={voice.name} value={voice.name}>
              {voice.display_name}
            </option>
          ))}
        </select>
        <input value={form.model_path} onChange={(event) => onChange({ ...form, model_path: event.target.value })} placeholder="model path" style={inputStyle} />
        <input value={form.index_path} onChange={(event) => onChange({ ...form, index_path: event.target.value })} placeholder="index path" style={inputStyle} />
        <input type="number" value={form.pitch_shift} onChange={(event) => onChange({ ...form, pitch_shift: Number(event.target.value) })} placeholder="pitch shift" style={inputStyle} />
        <input type="number" step="0.01" value={form.index_rate} onChange={(event) => onChange({ ...form, index_rate: Number(event.target.value) })} placeholder="index rate" style={inputStyle} />
        <select value={form.f0_method} onChange={(event) => onChange({ ...form, f0_method: event.target.value })} style={inputStyle}>
          <option value="rmvpe">rmvpe</option>
          <option value="crepe">crepe</option>
          <option value="harvest">harvest</option>
          <option value="dio">dio</option>
        </select>
        <input
          type="number"
          value={form.filter_radius}
          onChange={(event) => onChange({ ...form, filter_radius: Number(event.target.value) })}
          placeholder="filter radius"
          style={inputStyle}
        />
        <input
          type="number"
          value={form.resample_rate}
          onChange={(event) => onChange({ ...form, resample_rate: Number(event.target.value) })}
          placeholder="resample rate"
          style={inputStyle}
        />
        <input
          type="number"
          step="0.01"
          value={form.rms_mix_rate}
          onChange={(event) => onChange({ ...form, rms_mix_rate: Number(event.target.value) })}
          placeholder="rms mix rate"
          style={inputStyle}
        />
        <input
          type="number"
          step="0.01"
          value={form.protect_consonants}
          onChange={(event) => onChange({ ...form, protect_consonants: Number(event.target.value) })}
          placeholder="protect consonants"
          style={inputStyle}
        />
        <select
          value={form.gpu_device}
          onChange={(event) => onChange({ ...form, gpu_device: event.target.value, use_gpu: event.target.value !== "cpu" })}
          style={inputStyle}
        >
          <option value="auto">gpu auto</option>
          <option value="cpu">cpu</option>
          <option value="cuda">cuda</option>
          <option value="mps">mps</option>
        </select>
      </div>
      <button type="submit" style={{ ...primary, marginTop: 8 }}>
        Start convert job
      </button>
    </form>
  );
}
