export type Voice = {
  name: string;
  display_name: string;
  sample_rate: number;
  status: string;
  rvc_version: string;
  dataset_path?: string | null;
  base_model?: string | null;
};

export type Artifact = { type: string; path: string };

export type Job = {
  id: string;
  type: string;
  status: string;
  phase: string;
  progress: number;
  error?: string | null;
  artifacts: Artifact[];
};

export type DatasetSummary = {
  name: string;
  path: string;
  file_count: number;
  total_duration_seconds: number;
};

export type DatasetDetails = {
  summary: { name: string };
  files: { name: string; duration_seconds: number | null; valid: boolean; reason?: string | null }[];
};

export type DatasetPrepareResult = {
  dataset_name: string;
  source_path: string;
  prepared_path: string;
  file_count: number;
  created_count: number;
  skipped_count: number;
  total_duration_seconds: number;
  reused: boolean;
};

export type ModelInfo = { name: string; kind: string };

export type JobEvent = {
  id: number;
  job_id: string;
  level: string;
  message: string;
  created_at: string;
  data?: Record<string, unknown> | null;
};

export type JobLogs = {
  job_id: string;
  voice_name?: string | null;
  logs: Record<string, string>;
  metrics: { step: number; loss_gen?: number }[];
  events: JobEvent[];
};

export type Health = {
  status: string;
  device: string;
  ffmpeg_available: boolean;
  xtts_env_available: boolean;
  rvc_env_available: boolean;
  voices_count: number;
};

export type RuntimeSettings = { default_xtts_model?: string | null; default_rvc_model?: string | null };

export type GenerateForm = {
  voice: string;
  language: string;
  text: string;
  model: string;
  emotion: string;
  speed: number;
  temperature: number;
  top_k: number;
  top_p: number;
  repetition_penalty: number;
  pitch_shift: number;
  index_rate: number;
  f0_method: string;
  filter_radius: number;
  resample_rate: number;
  rms_mix_rate: number;
  protect_consonants: number;
  normalize: boolean;
  use_gpu: boolean;
  gpu_device: string;
};

export type ConvertForm = {
  input_path: string;
  voice: string;
  model_path: string;
  index_path: string;
  pitch_shift: number;
  index_rate: number;
  f0_method: string;
  filter_radius: number;
  resample_rate: number;
  rms_mix_rate: number;
  protect_consonants: number;
  use_gpu: boolean;
  gpu_device: string;
};

export type TrainForm = {
  voice_name: string;
  dataset_path: string;
  dataset_name: string;
  silence_slicing: boolean;
  normalize: boolean;
  min_audio_seconds: number;
  max_audio_seconds: number;
  segment_seconds: number;
  sample_rate: string;
  f0_method: string;
  epochs: number;
  batch_size: number;
  learning_rate: number;
  save_every_epoch: number;
  gpu_device: string;
  mixed_precision: boolean;
  version: string;
  use_gpu: boolean;
};
