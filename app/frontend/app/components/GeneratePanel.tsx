import { FormEvent } from "react";

import { GenerateForm, Voice } from "../types";
import { inputStyle, panel, primary } from "./styles";

type Props = {
  form: GenerateForm;
  voices: Voice[];
  latestAudio: string | null;
  onChange: (next: GenerateForm) => void;
  onSubmit: (event: FormEvent) => void;
};

const fieldDesc = {
  voice: "Qual voz usar para gerar (ex: api_probe4)",
  language: "Idioma do texto (português, inglês, espanhol)",
  model: "Deixa padrão - modelo XTTS",
  emotion: "Deixa em branco - emoção opcional",
  speed: "Velocidade: 1.0 = normal, 0.5 = lento, 1.5 = rápido",
  temperature: "Naturalidade: 0.7 = bom, 0.5 = robótico, 1.0 = mais variado",
  top_k: "Deixa padrão - criatividade",
  top_p: "Deixa padrão - diversidade",
  repetition_penalty: "Deixa padrão - evita repetição",
  pitch_shift: "Mudar tom de voz: 0 = normal, ±12 = semitom",
  index_rate: "Deixa padrão - força da voz",
  f0_method: "rmvpe = melhor, deixa assim",
  filter_radius: "Deixa padrão",
  resample_rate: "Deixa 0 (automático)",
  rms_mix_rate: "Deixa 1.0",
  protect_consonants: "Deixa 0.33",
  gpu_device: "auto = automático, cpu = sem GPU",
};

const FieldWithDesc = ({ label, desc, children }: { label: string; desc: string; children: React.ReactNode }) => (
  <div style={{ marginBottom: 12, paddingBottom: 12, borderBottom: "1px solid #eee" }}>
    <div style={{ fontWeight: "bold", color: "#333", marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: "12px", color: "#888", marginBottom: 8 }}>{desc}</div>
    {children}
  </div>
);

export function GeneratePanel({ form, voices, latestAudio, onChange, onSubmit }: Props) {
  return (
    <form onSubmit={onSubmit} style={panel}>
      <h2 style={{ marginTop: 0 }}>Gerar Áudio com Voz</h2>

      <div style={{ backgroundColor: "#f9f9f9", padding: "12px", borderRadius: "8px", marginBottom: "16px" }}>
        <strong>Importante:</strong> Mude apenas os campos em negrito abaixo. Os outros deixa no padrão!
      </div>

      <FieldWithDesc label="🎤 VOZ (IMPORTANTE!)" desc={fieldDesc.voice}>
        <select value={form.voice} onChange={(event) => onChange({ ...form, voice: event.target.value })} style={inputStyle}>
          <option value="">selecione uma voz</option>
          {voices.map((voice) => (
            <option key={voice.name} value={voice.name}>
              {voice.display_name}
            </option>
          ))}
        </select>
      </FieldWithDesc>

      <FieldWithDesc label="🗣️ IDIOMA" desc={fieldDesc.language}>
        <select value={form.language} onChange={(event) => onChange({ ...form, language: event.target.value })} style={inputStyle}>
          <option value="pt">Português</option>
          <option value="en">English</option>
          <option value="es">Español</option>
        </select>
      </FieldWithDesc>

      <FieldWithDesc label="📝 TEXTO A GERAR (IMPORTANTE!)" desc="Escreva aqui o que você quer que a voz fale">
        <textarea value={form.text} onChange={(event) => onChange({ ...form, text: event.target.value })} rows={5} style={{ ...inputStyle, resize: "vertical" }} placeholder="Olá, meu nome é..." />
      </FieldWithDesc>

      <div style={{ backgroundColor: "#f0f0f0", padding: "12px", borderRadius: "8px", marginBottom: "16px" }}>
        <strong>Configurações Avançadas (deixa padrão se não souber):</strong>
      </div>

      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
        <FieldWithDesc label="Velocidade (Speed)" desc={fieldDesc.speed}>
          <input type="number" step="0.05" value={form.speed} onChange={(event) => onChange({ ...form, speed: Number(event.target.value) })} style={inputStyle} />
        </FieldWithDesc>

        <FieldWithDesc label="Naturalidade (Temperature)" desc={fieldDesc.temperature}>
          <input type="number" step="0.05" value={form.temperature} onChange={(event) => onChange({ ...form, temperature: Number(event.target.value) })} style={inputStyle} />
        </FieldWithDesc>

        <FieldWithDesc label="Emoção" desc={fieldDesc.emotion}>
          <input value={form.emotion} onChange={(event) => onChange({ ...form, emotion: event.target.value })} placeholder="deixa vazio" style={inputStyle} />
        </FieldWithDesc>

        <FieldWithDesc label="Tom de Voz (Pitch)" desc={fieldDesc.pitch_shift}>
          <input type="number" value={form.pitch_shift} onChange={(event) => onChange({ ...form, pitch_shift: Number(event.target.value) })} style={inputStyle} />
        </FieldWithDesc>

        <FieldWithDesc label="F0 Method" desc={fieldDesc.f0_method}>
          <select value={form.f0_method} onChange={(event) => onChange({ ...form, f0_method: event.target.value })} style={inputStyle}>
            <option value="rmvpe">rmvpe (melhor)</option>
            <option value="crepe">crepe</option>
            <option value="harvest">harvest</option>
          </select>
        </FieldWithDesc>

        <FieldWithDesc label="GPU/CPU" desc={fieldDesc.gpu_device}>
          <select value={form.gpu_device} onChange={(event) => onChange({ ...form, gpu_device: event.target.value, use_gpu: event.target.value !== "cpu" })} style={inputStyle}>
            <option value="auto">Auto (recomendado)</option>
            <option value="cpu">CPU (lento)</option>
            <option value="cuda">CUDA</option>
          </select>
        </FieldWithDesc>
      </div>

      <button type="submit" style={{ ...primary, marginTop: 16, width: "100%", padding: "12px", fontSize: "16px" }}>
        Gerar Áudio
      </button>

      {latestAudio && (
        <div style={{ marginTop: 16, padding: "12px", backgroundColor: "#f0f0f0", borderRadius: "8px" }}>
          <strong>Áudio Gerado:</strong>
          <audio controls src={latestAudio} style={{ width: "100%", marginTop: 10 }} />
        </div>
      )}
    </form>
  );
}
