"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { ConvertPanel } from "./components/ConvertPanel";
import { DatasetsPanel } from "./components/DatasetsPanel";
import { GeneratePanel } from "./components/GeneratePanel";
import { JobsPanel } from "./components/JobsPanel";
import { ModelsPanel } from "./components/ModelsPanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { StudioStatusPanel } from "./components/StudioStatusPanel";
import { Tab, TabBar } from "./components/TabBar";
import { TrainPanel } from "./components/TrainPanel";
import { VoicesPanel } from "./components/VoicesPanel";
import { panel } from "./components/styles";
import {
  ConvertForm,
  DatasetDetails,
  DatasetPrepareResult,
  DatasetSummary,
  GenerateForm,
  Health,
  Job,
  JobEvent,
  JobLogs,
  ModelInfo,
  RuntimeSettings,
  TrainForm,
  Voice,
} from "./types";

const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<Tab>("Voice Studio");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [datasetDetails, setDatasetDetails] = useState<DatasetDetails | null>(null);
  const [jobLogs, setJobLogs] = useState<JobLogs | null>(null);
  const [runtimeSettings, setRuntimeSettings] = useState<RuntimeSettings>({});
  const [streamingJobId, setStreamingJobId] = useState<string | null>(null);
  const [liveEvents, setLiveEvents] = useState<JobEvent[]>([]);
  const streamRef = useRef<EventSource | null>(null);

  const [generateForm, setGenerateForm] = useState<GenerateForm>({
    voice: "",
    language: "pt",
    text: "Texto de teste para gerar voz local com XTTS e RVC.",
    model: "tts_models/multilingual/multi-dataset/xtts_v2",
    emotion: "",
    speed: 1.0,
    temperature: 0.7,
    top_k: 50,
    top_p: 0.8,
    repetition_penalty: 2.0,
    pitch_shift: 0,
    index_rate: 0.66,
    f0_method: "rmvpe",
    filter_radius: 3,
    resample_rate: 0,
    rms_mix_rate: 1.0,
    protect_consonants: 0.33,
    normalize: true,
    use_gpu: true,
    gpu_device: "auto",
  });
  const [convertForm, setConvertForm] = useState<ConvertForm>({
    input_path: "",
    voice: "",
    model_path: "",
    index_path: "",
    pitch_shift: 0,
    index_rate: 0.66,
    f0_method: "rmvpe",
    filter_radius: 3,
    resample_rate: 0,
    rms_mix_rate: 1.0,
    protect_consonants: 0.33,
    use_gpu: true,
    gpu_device: "auto",
  });
  const [trainForm, setTrainForm] = useState<TrainForm>({
    voice_name: "",
    dataset_path: ".",
    dataset_name: "",
    silence_slicing: true,
    normalize: true,
    min_audio_seconds: 0,
    max_audio_seconds: 0,
    segment_seconds: 12,
    sample_rate: "40k",
    f0_method: "rmvpe",
    epochs: 300,
    batch_size: 1,
    learning_rate: 0.0001,
    save_every_epoch: 10,
    gpu_device: "auto",
    mixed_precision: false,
    version: "v2",
    use_gpu: true,
  });
  const [datasetUploadName, setDatasetUploadName] = useState("default");
  const [datasetUploadFile, setDatasetUploadFile] = useState<File | null>(null);
  const [audioUploadFile, setAudioUploadFile] = useState<File | null>(null);
  const [modelDownloadUrl, setModelDownloadUrl] = useState("");

  async function api(path: string, init?: RequestInit) {
    const response = await fetch(`${apiBase}${path}`, { cache: "no-store", ...init });
    const text = await response.text();
    const body = text ? JSON.parse(text) : {};
    if (!response.ok) throw new Error(body.detail ?? `HTTP ${response.status}`);
    return body;
  }

  function ok(message: string) {
    setError("");
    setStatus(message);
  }

  function fail(err: unknown) {
    setStatus("");
    setError(err instanceof Error ? err.message : String(err));
  }

  function stopStream() {
    if (streamRef.current) {
      streamRef.current.close();
      streamRef.current = null;
    }
    setStreamingJobId(null);
  }

  function toggleStream(jobId: string) {
    if (streamingJobId === jobId) {
      stopStream();
      return;
    }
    stopStream();
    setLiveEvents([]);
    const source = new EventSource(`${apiBase}/jobs/${jobId}/stream`);
    source.addEventListener("job_event", (event) => {
      const payload = JSON.parse((event as MessageEvent).data) as JobEvent;
      setLiveEvents((prev) => [...prev.slice(-199), payload]);
    });
    source.addEventListener("job_done", () => {
      refreshJobsOnly().catch(fail);
      source.close();
      streamRef.current = null;
      setStreamingJobId(null);
    });
    source.onerror = () => {
      source.close();
      streamRef.current = null;
      setStreamingJobId(null);
    };
    streamRef.current = source;
    setStreamingJobId(jobId);
  }

  async function refreshJobsOnly() {
    const jobsData = (await api("/jobs")) as { jobs?: Job[] };
    setJobs(jobsData.jobs ?? []);
  }

  async function refreshAll() {
    const [healthData, voicesData, jobsData, datasetsData, modelsData, settingsData] = await Promise.all([
      api("/health"),
      api("/voices"),
      api("/jobs"),
      api("/datasets"),
      api("/models"),
      api("/settings"),
    ]);
    setHealth(healthData as Health);
    const voicesPayload = (voicesData as { voices?: Voice[] }).voices ?? [];
    setVoices(voicesPayload);
    setJobs((jobsData as { jobs?: Job[] }).jobs ?? []);
    setDatasets((datasetsData as { datasets?: DatasetSummary[] }).datasets ?? []);
    setModels((modelsData as { models?: ModelInfo[] }).models ?? []);
    setRuntimeSettings(settingsData as RuntimeSettings);
    if (!generateForm.voice && voicesPayload.length) setGenerateForm((prev) => ({ ...prev, voice: voicesPayload[0].name }));
    if (!convertForm.voice && voicesPayload.length) setConvertForm((prev) => ({ ...prev, voice: voicesPayload[0].name }));
  }

  useEffect(() => {
    refreshAll().catch(fail);
    const timer = setInterval(() => refreshJobsOnly().catch(fail), 3000);
    return () => {
      clearInterval(timer);
      stopStream();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const latestAudio = useMemo(() => {
    const completed = jobs.find((job) => (job.type === "generate_voice" || job.type === "convert_voice") && job.status === "completed");
    if (!completed) return null;
    const item = completed.artifacts.find((artifact) => artifact.type === "audio/wav");
    const file = item?.path.split(/[\\/]/).pop();
    return file ? `${apiBase}/audio/${file}` : null;
  }, [jobs]);

  async function submitGenerate(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/generate_voice", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(generateForm) });
      ok("Generate job enviado.");
      refreshJobsOnly().catch(fail);
    } catch (exc) {
      fail(exc);
    }
  }

  async function submitTrain(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/train_voice", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(trainForm) });
      ok("Train job enviado.");
      refreshJobsOnly().catch(fail);
    } catch (exc) {
      fail(exc);
    }
  }

  async function submitConvert(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/convert_voice", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(convertForm) });
      ok("Convert job enviado.");
      refreshJobsOnly().catch(fail);
    } catch (exc) {
      fail(exc);
    }
  }

  async function uploadInputAudio() {
    if (!audioUploadFile) return;
    const upload = (await api(`/audio/upload?filename=${encodeURIComponent(audioUploadFile.name)}`, {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: await audioUploadFile.arrayBuffer(),
    })) as { path: string };
    setConvertForm((prev) => ({ ...prev, input_path: upload.path }));
    ok("audio enviado");
  }

  async function validateDataset() {
    const details = (await api("/datasets/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_path: trainForm.dataset_name ? trainForm.dataset_name : trainForm.dataset_path,
        min_audio_seconds: trainForm.min_audio_seconds,
        max_audio_seconds: trainForm.max_audio_seconds,
      }),
    })) as DatasetDetails;
    setDatasetDetails(details);
    ok("dataset validado");
  }

  async function prepareDataset() {
    if (!trainForm.dataset_name) {
      throw new Error("dataset_name is required to prepare dataset.");
    }
    const prepared = (await api("/datasets/prepare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_name: trainForm.dataset_name,
        silence_trimming: trainForm.silence_slicing,
        normalization: trainForm.normalize,
        auto_segmentation: true,
        segment_seconds: trainForm.segment_seconds,
      }),
    })) as DatasetPrepareResult;
    setTrainForm((prev) => ({ ...prev, dataset_path: prepared.prepared_path }));
    ok(`dataset preparado: ${prepared.file_count} arquivos`);
  }

  async function uploadDataset() {
    if (!datasetUploadFile) return;
    await api(`/datasets/upload?dataset_name=${encodeURIComponent(datasetUploadName)}&filename=${encodeURIComponent(datasetUploadFile.name)}`, {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: await datasetUploadFile.arrayBuffer(),
    });
    ok("dataset enviado");
    await refreshAll();
  }

  async function fetchDatasetDetails(datasetName: string) {
    const details = (await api(`/datasets/${encodeURIComponent(datasetName)}`)) as DatasetDetails;
    setDatasetDetails(details);
  }

  async function fetchJobLogs(jobId: string) {
    const logs = (await api(`/jobs/${jobId}/logs`)) as JobLogs;
    setJobLogs(logs);
  }

  async function deleteVoice(voiceName: string) {
    await api(`/voices/${encodeURIComponent(voiceName)}`, { method: "DELETE" });
    await refreshAll();
  }

  async function downloadModel() {
    await api("/models/download", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: modelDownloadUrl }) });
    setModelDownloadUrl("");
    ok("modelo baixado");
    await refreshAll();
  }

  async function deleteModel(modelName: string) {
    await api(`/models/${encodeURIComponent(modelName)}`, { method: "DELETE" });
    await refreshAll();
  }

  async function saveSettings() {
    const saved = (await api("/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        default_xtts_model: runtimeSettings.default_xtts_model,
        default_rvc_model: runtimeSettings.default_rvc_model,
      }),
    })) as RuntimeSettings;
    setRuntimeSettings(saved);
    ok("settings salvas.");
  }

  return (
    <main style={{ maxWidth: 1180, margin: "0 auto", padding: "48px 20px 80px" }}>
      <section style={{ marginBottom: 24 }}>
        <div style={{ display: "inline-block", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: 999, color: "var(--muted)" }}>Voice Studio</div>
        <h1 style={{ fontSize: "clamp(2.4rem, 7vw, 5.2rem)", lineHeight: 0.95, margin: "16px 0 10px" }}>
          XTTS + RVC
          <br />
          local voice engine
        </h1>
      </section>

      <TabBar activeTab={activeTab} onSelect={setActiveTab} />

      {(status || error) && (
        <section style={{ ...panel, marginBottom: 14 }}>
          {status ? <div style={{ color: "#205a2b" }}>{status}</div> : null}
          {error ? <div style={{ color: "#8b1e1e" }}>{error}</div> : null}
        </section>
      )}

      {activeTab === "Voice Studio" && <StudioStatusPanel health={health} />}
      {activeTab === "Generate" && <GeneratePanel form={generateForm} voices={voices} latestAudio={latestAudio} onChange={setGenerateForm} onSubmit={submitGenerate} />}
      {activeTab === "Convert" && (
        <ConvertPanel
          form={convertForm}
          voices={voices}
          audioUploadFile={audioUploadFile}
          onAudioUploadFileChange={setAudioUploadFile}
          onChange={setConvertForm}
          onUploadAudio={async () => uploadInputAudio().catch(fail)}
          onSubmit={submitConvert}
        />
      )}
      {activeTab === "Train" && (
        <TrainPanel
          form={trainForm}
          onChange={setTrainForm}
          onValidateDataset={async () => validateDataset().catch(fail)}
          onPrepareDataset={async () => prepareDataset().catch(fail)}
          onSubmit={submitTrain}
        />
      )}
      {activeTab === "Datasets" && (
        <DatasetsPanel
          datasets={datasets}
          datasetDetails={datasetDetails}
          datasetUploadName={datasetUploadName}
          datasetUploadFile={datasetUploadFile}
          onDatasetUploadNameChange={setDatasetUploadName}
          onDatasetUploadFileChange={setDatasetUploadFile}
          onUploadDataset={async () => uploadDataset().catch(fail)}
          onPreviewDataset={async (name) => fetchDatasetDetails(name).catch(fail)}
        />
      )}
      {activeTab === "Voices" && <VoicesPanel apiBase={apiBase} voices={voices} onDeleteVoice={async (name) => deleteVoice(name).catch(fail)} />}
      {activeTab === "Models" && (
        <ModelsPanel
          modelDownloadUrl={modelDownloadUrl}
          models={models}
          onModelDownloadUrlChange={setModelDownloadUrl}
          onDownloadModel={async () => downloadModel().catch(fail)}
          onDeleteModel={async (name) => deleteModel(name).catch(fail)}
        />
      )}
      {activeTab === "Jobs" && (
        <JobsPanel
          jobs={jobs}
          jobLogs={jobLogs}
          liveEvents={liveEvents}
          streamingJobId={streamingJobId}
          onFetchLogs={async (jobId) => fetchJobLogs(jobId).catch(fail)}
          onToggleStream={(jobId) => toggleStream(jobId)}
        />
      )}
      {activeTab === "Settings" && (
        <SettingsPanel apiBase={apiBase} health={health} settings={runtimeSettings} onChange={setRuntimeSettings} onSave={async () => saveSettings().catch(fail)} />
      )}
    </main>
  );
}
