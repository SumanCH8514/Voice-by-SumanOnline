export type TabType = 
  | 'studio' 
  | 'presets' 
  | 'dictionary' 
  | 'history' 
  | 'audio' 
  | 'engine' 
  | 'shortcuts' 
  | 'install';

export type StylePresetId = 
  | 'smart' 
  | 'executive' 
  | 'casual' 
  | 'notes' 
  | 'code' 
  | 'custom';

export interface StylePreset {
  id: StylePresetId;
  name: string;
  tagline: string;
  description: string;
  badge: string;
  iconName: string;
}

export interface HistoryEntry {
  id: string;
  timestamp: string;
  raw_text: string;
  cleaned_text: string;
  preset: string;
  tier: string;
  audio_duration_s: number;
  latency_s: number;
  word_count: number;
}

export interface StatsSummary {
  total_dictations: number;
  total_words: number;
  total_audio_seconds: number;
  estimated_minutes_saved: number;
  recent_count: number;
}

export interface AudioDevice {
  index: number;
  name: string;
  channels: number;
  sample_rate: number;
  is_default: boolean;
}

export interface AppConfig {
  hotkey: string;
  toggle_mode: boolean;
  pre_roll_ms: number;
  input_device: number | string | null;
  overlay_enabled: boolean;
  start_on_login: boolean;
  style_preset: StylePresetId;
  custom_prompt: string;
  has_key?: boolean;
  transcription: {
    model: string;
    preview_enabled: boolean;
  };
  format: {
    tier: string;
    groq_model: string;
    ollama_model: string;
  };
  dictionary: [string, string][];
  stats: {
    total_dictations: number;
    total_words: number;
    total_seconds_recorded: number;
  };
}

export interface AppStatus {
  status: string;
  app_name: string;
  has_key: boolean;
  style_preset: StylePresetId;
  toggle_mode: boolean;
  hotkey: string;
  whisper_model: string;
  preview_enabled: boolean;
  is_recording?: boolean;
  is_processing?: boolean;
  muted?: boolean;
}
