import React, { useState, useEffect } from 'react';
import { 
  fetchConfig, 
  fetchStatus, 
  createLiveWebSocket, 
  triggerManualRecording, 
  triggerToggleMute,
  updateConfig
} from './services/api';
import { AppConfig, AppStatus, StylePresetId, TabType } from './types';
import { Sidebar } from './components/Sidebar';
import { FloatingHud } from './components/FloatingHud';
import { VoiceStudio } from './components/VoiceStudio';
import { StylePresets } from './components/StylePresets';
import { DictionaryManager } from './components/DictionaryManager';
import { HistoryAnalytics } from './components/HistoryAnalytics';
import { AudioSettings } from './components/AudioSettings';
import { EngineSettings } from './components/EngineSettings';
import { ShortcutsSettings } from './components/ShortcutsSettings';
import { InstallationGuide } from './components/InstallationGuide';
import { Radio, VolumeX, Shield, Wifi } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('studio');
  const [config, setConfig] = useState<AppConfig>({
    hotkey: 'Key.alt_r',
    toggle_mode: false,
    pre_roll_ms: 0,
    input_device: null,
    overlay_enabled: true,
    start_on_login: false,
    style_preset: 'smart',
    custom_prompt: '',
    transcription: { model: 'base', preview_enabled: true },
    format: { tier: 'auto', groq_model: 'qwen/qwen3.8-27b', ollama_model: 'llama3.2:3b' },
    dictionary: [],
    stats: { total_dictations: 0, total_words: 0, total_seconds_recorded: 0 },
  });
  const [hasKey, setHasKey] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [rms, setRms] = useState(0);
  const [rmsBars, setRmsBars] = useState<number[]>([0, 0, 0, 0, 0]);
  const [previewText, setPreviewText] = useState('');
  const [statusText, setStatusText] = useState('');
  const [lastRaw, setLastRaw] = useState('');
  const [lastCleaned, setLastCleaned] = useState('');
  const [latencyBreakdown, setLatencyBreakdown] = useState({
    audio_s: 0,
    whisper_s: 0,
    format_s: 0,
    total_s: 0,
    tier: '',
  });

  useEffect(() => {
    fetchConfig()
      .then((cfg) => {
        setConfig(cfg);
        if (cfg.has_key !== undefined) setHasKey(cfg.has_key);
      })
      .catch(() => {});

    fetchStatus()
      .then((st) => {
        setHasKey(st.has_key);
        setIsMuted(bool(st.muted));
        if (st.is_recording) setIsRecording(true);
        if (st.is_processing) setIsProcessing(true);
      })
      .catch(() => {});

    const ws = createLiveWebSocket((msg: any) => {
      if (msg.type === 'state_changed') {
        if (msg.state === 'recording') {
          setIsRecording(true);
          setIsProcessing(false);
          setPreviewText('');
        } else if (msg.state === 'processing') {
          setIsRecording(false);
          setIsProcessing(true);
        } else if (msg.state === 'idle') {
          setIsRecording(false);
          setIsProcessing(false);
          setPreviewText('');
        }
      } else if (msg.type === 'audio_rms') {
        setRms(msg.rms || 0);
        if (msg.rms_bars) setRmsBars(msg.rms_bars);
      } else if (msg.type === 'preview_text') {
        setPreviewText(msg.text || '');
      } else if (msg.type === 'raw_transcript') {
        setLastRaw(msg.text || '');
      } else if (msg.type === 'final_result') {
        setLastRaw(msg.raw || '');
        setLastCleaned(msg.cleaned || '');
        setLatencyBreakdown({
          audio_s: msg.audio_duration_s || 0,
          whisper_s: msg.whisper_s || 0,
          format_s: msg.format_s || 0,
          total_s: msg.latency_s || 0,
          tier: msg.tier || '',
        });
      } else if (msg.type === 'mute_changed') {
        setIsMuted(bool(msg.muted));
      } else if (msg.type === 'config_updated') {
        if (msg.config) setConfig(msg.config);
      }
    });

    return () => {
      ws.close();
    };
  }, []);

  function bool(v: any): boolean {
    return v === true || v === 'true';
  }

  const handleToggleMute = async () => {
    try {
      const res = await triggerToggleMute();
      setIsMuted(res.muted);
    } catch {}
  };

  const handleToggleRecording = async () => {
    try {
      const res = await triggerManualRecording();
      if (res.state === 'recording') {
        setIsRecording(true);
        setIsProcessing(false);
      } else if (res.state === 'processing') {
        setIsRecording(false);
        setIsProcessing(true);
      }
    } catch {}
  };

  const handleSelectPreset = async (presetId: StylePresetId) => {
    try {
      const res = await updateConfig({ style_preset: presetId });
      if (res.success) {
        setConfig(res.config);
      }
    } catch {}
  };

  return (
    <div className="flex h-screen bg-[#080C14] text-slate-100 overflow-hidden font-sans">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isRecording={isRecording}
        isProcessing={isProcessing}
        isMuted={isMuted}
        onToggleMute={handleToggleMute}
        onToggleRecording={handleToggleRecording}
      />

      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <header className="h-16 border-b border-white/5 bg-[#0B0F19]/60 backdrop-blur-md px-8 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs font-medium text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-white font-semibold">Engine Online</span>
              <span className="text-slate-600">•</span>
              <span className="font-mono text-slate-400">Port 48922</span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <FloatingHud
              isRecording={isRecording}
              isProcessing={isProcessing}
              rms={rms}
              rmsBars={rmsBars}
              previewText={previewText}
              statusText={statusText}
              stylePreset={config.style_preset || 'smart'}
            />

            {isMuted && (
              <div className="flex items-center space-x-1.5 px-3 py-1 rounded-xl bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs font-semibold">
                <VolumeX className="w-3.5 h-3.5 text-amber-400" />
                <span>Muted</span>
              </div>
            )}
          </div>
        </header>

        <section className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-6xl mx-auto pb-12">
            {activeTab === 'studio' && (
              <VoiceStudio
                config={config}
                isRecording={isRecording}
                isProcessing={isProcessing}
                rms={rms}
                previewText={previewText}
                lastRaw={lastRaw}
                lastCleaned={lastCleaned}
                latencyBreakdown={latencyBreakdown}
                onToggleRecording={handleToggleRecording}
                onSelectPreset={handleSelectPreset}
              />
            )}

            {activeTab === 'presets' && (
              <StylePresets
                config={config}
                onConfigChange={setConfig}
              />
            )}

            {activeTab === 'dictionary' && (
              <DictionaryManager
                config={config}
                onConfigChange={setConfig}
              />
            )}

            {activeTab === 'history' && (
              <HistoryAnalytics />
            )}

            {activeTab === 'audio' && (
              <AudioSettings
                config={config}
                rms={rms}
                onConfigChange={setConfig}
              />
            )}

            {activeTab === 'engine' && (
              <EngineSettings
                config={config}
                hasKey={hasKey}
                onConfigChange={setConfig}
                onKeyStatusChange={setHasKey}
              />
            )}

            {activeTab === 'shortcuts' && (
              <ShortcutsSettings
                config={config}
                onConfigChange={setConfig}
              />
            )}

            {activeTab === 'install' && (
              <InstallationGuide
                config={config}
                hasKey={hasKey}
              />
            )}
          </div>
        </section>
      </main>
    </div>
  );
};
