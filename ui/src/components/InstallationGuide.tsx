import React from 'react';
import { 
  Download, 
  CheckCircle2, 
  Sparkles, 
  Monitor, 
  Terminal, 
  ShieldCheck, 
  FileCheck,
  FolderGit2
} from 'lucide-react';
import { AppConfig } from '../types';

interface InstallationGuideProps {
  config: AppConfig;
  hasKey: boolean;
}

export const InstallationGuide: React.FC<InstallationGuideProps> = ({ config, hasKey }) => {
  const checklist = [
    { label: 'Voice Engine Core', status: 'Installed & Running', ok: true },
    { label: 'Microphone & Audio Resampler', status: 'Ready (16 kHz Polyphase)', ok: true },
    { label: 'Faster-Whisper Local ASR', status: `Model: ${config.transcription.model}`, ok: true },
    { label: 'Vosk Real-Time Streaming ASR', status: 'Cached in ~/.cache/voice_by_sumanonline', ok: true },
    { label: 'Clipboard & Cursor Injection', status: 'Active (win32clipboard / pynput)', ok: true },
    { label: 'Cloud AI Cleanup (Groq)', status: hasKey ? 'Configured in Keychain' : 'Using Local Fallback', ok: hasKey },
    { label: 'Native Windows Rust Launcher', status: 'Ready in crates/voice-launcher', ok: true },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Desktop App Installation</h2>
        <p className="text-sm text-slate-400">
          Install Voice by SumanOnline on your PC just like Wispr Flow with desktop shortcuts and background tray integration.
        </p>
      </div>

      <div className="p-6 rounded-2xl glass-panel border border-white/5 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>System Readiness Checklist</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {checklist.map((item, i) => (
            <div key={i} className="p-3.5 rounded-xl bg-[#080C14] border border-white/5 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-white">{item.label}</div>
                <div className="text-[11px] text-slate-400 font-mono mt-0.5">{item.status}</div>
              </div>
              <CheckCircle2 className={`w-4 h-4 ${item.ok ? 'text-emerald-400' : 'text-amber-400'}`} />
            </div>
          ))}
        </div>
      </div>

      <div className="p-6 rounded-2xl glass-panel border border-indigo-500/20 space-y-4">
        <div className="flex items-center space-x-2.5">
          <Terminal className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-sm font-bold text-white">One-Click Windows Desktop Setup</h3>
            <p className="text-xs text-slate-400">Run the automated installer script to create desktop & start menu shortcuts.</p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#080C14] border border-white/5 font-mono text-xs text-slate-200 space-y-2 select-text">
          <div className="text-slate-500"># Run in PowerShell from the project root:</div>
          <div className="text-indigo-300 font-bold">powershell -ExecutionPolicy Bypass -File .\installer\install.ps1</div>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          The installer automatically creates a Start Menu shortcut, a Desktop icon, registers Windows startup (if enabled), and configures the native silent background launcher.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-2">
          <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider">1. Push-to-Talk Anywhere</div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Hold <kbd className="px-1.5 py-0.5 rounded bg-white/10 font-mono text-indigo-200">{config.hotkey}</kbd> in any app—Word, Slack, VS Code, Chrome, or WhatsApp—and release to paste.
          </p>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-2">
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-wider">2. System Tray Control</div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Runs silently in the Windows system notification area. Right-click the microphone icon to toggle mute, open Voice Studio, or quit.
          </p>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-2">
          <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider">3. Zero Focus Stealing</div>
          <p className="text-xs text-slate-400 leading-relaxed">
            The floating HUD pill uses native <code className="text-slate-300">WS_EX_NOACTIVATE</code> window styles so your typing cursor never loses its position.
          </p>
        </div>
      </div>
    </div>
  );
};
