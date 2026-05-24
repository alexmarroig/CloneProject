import { FormEvent } from "react";

import { TrainForm } from "../types";
import { ghost, inputStyle, panel, primary } from "./styles";

type Props = {
  form: TrainForm;
  onChange: (next: TrainForm) => void;
  onValidateDataset: () => Promise<void>;
  onPrepareDataset: () => Promise<void>;
  onSubmit: (event: FormEvent) => void;
};

export function TrainPanel({ form, onChange, onValidateDataset, onPrepareDataset, onSubmit }: Props) {
  return (
    <form onSubmit={onSubmit} style={panel}>
      <h2 style={{ marginTop: 0 }}>Train</h2>
      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))" }}>
        <input value={form.voice_name} onChange={(event) => onChange({ ...form, voice_name: event.target.value })} placeholder="voice name" style={inputStyle} />
        <input value={form.dataset_name} onChange={(event) => onChange({ ...form, dataset_name: event.target.value })} placeholder="dataset name" style={inputStyle} />
        <input value={form.dataset_path} onChange={(event) => onChange({ ...form, dataset_path: event.target.value })} placeholder="dataset path" style={inputStyle} />
        <select value={form.sample_rate} onChange={(event) => onChange({ ...form, sample_rate: event.target.value })} style={inputStyle}>
          <option value="32k">32k</option>
          <option value="40k">40k</option>
          <option value="48k">48k</option>
        </select>
        <select value={form.f0_method} onChange={(event) => onChange({ ...form, f0_method: event.target.value })} style={inputStyle}>
          <option value="rmvpe">rmvpe</option>
          <option value="crepe">crepe</option>
          <option value="harvest">harvest</option>
          <option value="dio">dio</option>
        </select>
        <input type="number" value={form.epochs} onChange={(event) => onChange({ ...form, epochs: Number(event.target.value) })} placeholder="epochs" style={inputStyle} />
        <input type="number" value={form.batch_size} onChange={(event) => onChange({ ...form, batch_size: Number(event.target.value) })} placeholder="batch size" style={inputStyle} />
        <input
          type="number"
          step="0.00001"
          value={form.learning_rate}
          onChange={(event) => onChange({ ...form, learning_rate: Number(event.target.value) })}
          placeholder="learning rate"
          style={inputStyle}
        />
        <input
          type="number"
          value={form.save_every_epoch}
          onChange={(event) => onChange({ ...form, save_every_epoch: Number(event.target.value) })}
          placeholder="save every epoch"
          style={inputStyle}
        />
        <select
          value={form.gpu_device}
          onChange={(event) => onChange({ ...form, gpu_device: event.target.value, use_gpu: event.target.value !== "cpu" })}
          style={inputStyle}
        >
          <option value="auto">auto</option>
          <option value="cpu">cpu</option>
          <option value="cuda">cuda</option>
          <option value="mps">mps</option>
        </select>
        <input
          type="number"
          step="0.1"
          value={form.min_audio_seconds}
          onChange={(event) => onChange({ ...form, min_audio_seconds: Number(event.target.value) })}
          placeholder="min audio length"
          style={inputStyle}
        />
        <input
          type="number"
          step="0.1"
          value={form.max_audio_seconds}
          onChange={(event) => onChange({ ...form, max_audio_seconds: Number(event.target.value) })}
          placeholder="max audio length"
          style={inputStyle}
        />
        <input
          type="number"
          value={form.segment_seconds}
          onChange={(event) => onChange({ ...form, segment_seconds: Number(event.target.value) })}
          placeholder="segment seconds"
          style={inputStyle}
        />
      </div>
      <div style={{ marginTop: 8, display: "flex", gap: 10, flexWrap: "wrap" }}>
        <label>
          <input type="checkbox" checked={form.silence_slicing} onChange={(event) => onChange({ ...form, silence_slicing: event.target.checked })} /> silence slicing
        </label>
        <label>
          <input type="checkbox" checked={form.normalize} onChange={(event) => onChange({ ...form, normalize: event.target.checked })} /> normalization
        </label>
        <label>
          <input type="checkbox" checked={form.mixed_precision} onChange={(event) => onChange({ ...form, mixed_precision: event.target.checked })} /> mixed precision
        </label>
        <button type="button" style={ghost} onClick={() => onValidateDataset()}>
          Dataset validation
        </button>
        <button type="button" style={ghost} onClick={() => onPrepareDataset()}>
          Prepare dataset
        </button>
      </div>
      <button type="submit" style={{ ...primary, marginTop: 8 }}>
        Start training job
      </button>
    </form>
  );
}
