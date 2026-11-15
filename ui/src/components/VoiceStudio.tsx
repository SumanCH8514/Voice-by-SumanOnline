import React, { useState } from 'react';
import { 
  Mic, 
  Square, 
  Sparkles, 
  Copy, 
  Check, 
  Clock, 
  Cpu, 
  Zap, 
  ArrowRight,
  ShieldCheck,
  Flame,
  Volume2
} from 'lucide-react';
import { AppConfig, StylePresetId } from '../types';

interface VoiceStudioProps {
  config: AppConfig;
  isRecording: boolean;
  isProcessing: boolean;
  rms: number;
  previewText: string;
  lastRaw: string;
  lastCleaned: string;
  latencyBreakdown: {
    audio_s: number;
    whisper_s: number;
    format_s: number;
    total_s: number;
    tier: string;
  };
  onToggleRecording: () => void;
  onSelectPreset: (preset: StylePresetId) => void;
}

export const VoiceStudio: React.FC<VoiceStudioProps> = ({
  config,
  isRecording,
  isProcessing,
  rms,
  previewText,
  lastRaw,
  lastCleaned,
  latencyBreakdown,
  onToggleRecording,
  onSelectPreset,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!lastCleaned) return;
    navigator.clipboard.writeText(lastCleaned);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const presets: { id: StylePresetId; name: string }[] = [
    { id: 'smart', name: 'Smart Dictation' },
    { id: 'executive', name: 'Executive' },
    { id: 'casual', name: 'Casual' },
    { id: 'notes', name: 'Bullet Notes' },
    { id: 'code', name: 'Developer / Code' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Voice Studio</h2>
          <p className="text-sm text-slate-400">
            Real-time dictation playground and live acoustic telemetry.
          </p>
        </div>

        <div className="flex items-center space-x-1 p-1 bg-slate-900/90 border border-white/5 rounded-xl">
          {presets.map((p) => {
            const isSelected = config.style_preset === p.id;
            return (
              <button
                key={p.id}
                onClick={() => onSelectPreset(p.id)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                  isSelected
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
                }`}
              >
                {p.name}
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-8 rounded-2xl glass-panel relative overflow-hidden border border-white/10 shadow-2xl">
        <div className="absolute top-0 right-0 p-8 pointer-events-none opacity-10">
          <Sparkles className="w-48 h-48 text-indigo-400" />
        </div>

        <div className="max-w-xl mx-auto text-center space-y-6">
          <div className="relative inline-block">
            <button
              onClick={onToggleRecording}
              className={`w-24 h-24 rounded-3xl flex flex-col items-center justify-center transition-all duration-300 transform active:scale-95 shadow-2xl ${
                isRecording
                  ? 'bg-rose-500 text-white shadow-rose-500/40 ring-4 ring-rose-400/30 animate-pulse'
                  : isProcessing
                  ? 'bg-amber-500 text-white shadow-amber-500/40 ring-4 ring-amber-400/30'
                  : 'bg-gradient-to-tr from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-indigo-500/30'
              }`}
            >
              {isRecording ? (
                <Square className="w-8 h-8 fill-current" />
              ) : isProcessing ? (
                <Zap className="w-8 h-8 animate-bounce" />
              ) : (
                <Mic className="w-8 h-8" />
              )}
              <span className="text-[10px] font-bold uppercase tracking-wider mt-1.5">
                {isRecording ? 'Stop' : isProcessing ? 'Polishing' : 'Dictate'}
              </span>
            </button>

            {isRecording && (
              <div 
                className="absolute inset-0 rounded-3xl border-2 border-indigo-400 pointer-events-none transition-all duration-75"
                style={{ transform: `scale(${1 + rms * 2.5})`, opacity: Math.min(1, rms * 5) }}
              />
            )}
          </div>

          <div>
            <div className="text-base font-semibold text-white">
              {isRecording
                ? 'Listening to microphone...'
                : isProcessing
                ? 'Processing with Faster-Whisper & AI...'
                : 'Hold or Click to Speak'}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Global Hotkey: <kbd className="px-2 py-0.5 rounded bg-white/10 font-mono text-indigo-300 border border-white/10">{config.hotkey || 'Right Alt'}</kbd>
              {' '}• Auto-pastes at your system cursor without stealing focus.
            </p>
          </div>

          {previewText && (
            <div className="p-4 rounded-xl bg-slate-900/90 border border-indigo-500/30 text-left animate-fadeIn">
              <div className="flex items-center space-x-2 text-[11px] font-semibold text-indigo-400 uppercase tracking-wider mb-1">
                <Volume2 className="w-3.5 h-3.5 animate-pulse" />
                <span>Live Streaming Preview (Vosk)</span>
              </div>
              <p className="text-sm text-slate-200 font-medium">
                {previewText}
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Total Latency</div>
            <div className="text-lg font-bold text-white font-mono">{latencyBreakdown.total_s > 0 ? `${latencyBreakdown.total_s}s` : '—'}</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Whisper ({config.transcription.model})</div>
            <div className="text-lg font-bold text-white font-mono">{latencyBreakdown.whisper_s > 0 ? `${latencyBreakdown.whisper_s}s` : '—'}</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">AI Cleanup ({latencyBreakdown.tier || 'Groq'})</div>
            <div className="text-lg font-bold text-white font-mono">{latencyBreakdown.format_s > 0 ? `${latencyBreakdown.format_s}s` : '—'}</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-white/5 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">Spoken Audio</div>
            <div className="text-lg font-bold text-white font-mono">{latencyBreakdown.audio_s > 0 ? `${latencyBreakdown.audio_s}s` : '—'}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Raw Whisper Transcription</h3>
            </div>
            <span className="text-[11px] text-slate-500 font-mono">Unfiltered</span>
          </div>
          <div className="min-h-[140px] p-4 rounded-xl bg-[#080C14] border border-white/5 text-sm text-slate-300 font-mono leading-relaxed select-text">
            {lastRaw || <span className="text-slate-600 italic">Dictated audio transcript will appear here...</span>}
          </div>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-indigo-500/20 shadow-lg shadow-indigo-500/5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Flame className="w-4 h-4 text-indigo-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300">Cleaned & Formatted Output</h3>
            </div>
            {lastCleaned && (
              <button
                onClick={handleCopy}
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 text-xs font-medium transition-colors"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            )}
          </div>
          <div className="min-h-[140px] p-4 rounded-xl bg-[#080C14] border border-indigo-500/20 text-sm text-white font-sans leading-relaxed select-text shadow-inner">
            {lastCleaned || <span className="text-slate-600 italic">Polished output with fillers stripped and punctuation resolved...</span>}
          </div>
        </div>
      </div>
    </div>
  );
};
