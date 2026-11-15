import React, { useState } from 'react';
import { 
  Cpu, 
  Key, 
  Sparkles, 
  ShieldCheck, 
  Check, 
  AlertCircle, 
  RefreshCw, 
  Zap, 
  Layers, 
  Server 
} from 'lucide-react';
import { AppConfig } from '../types';
import { saveApiKey, testApiKey, updateConfig } from '../services/api';

interface EngineSettingsProps {
  config: AppConfig;
  hasKey: boolean;
  onConfigChange: (newConfig: AppConfig) => void;
  onKeyStatusChange: (hasKey: boolean) => void;
}

export const EngineSettings: React.FC<EngineSettingsProps> = ({
  config,
  hasKey,
  onConfigChange,
  onKeyStatusChange,
}) => {
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [testingKey, setTestingKey] = useState(false);
  const [keyTestResult, setKeyTestResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const [whisperModel, setWhisperModel] = useState(config.transcription.model || 'base');
  const [previewEnabled, setPreviewEnabled] = useState(config.transcription.preview_enabled !== false);
  const [groqModel, setGroqModel] = useState(config.format.groq_model || 'qwen/qwen3.8-27b');
  const [ollamaModel, setOllamaModel] = useState(config.format.ollama_model || 'llama3.2:3b');
  const [tierChoice, setTierChoice] = useState(config.format.tier || 'auto');

  const handleSaveKey = async () => {
    if (!apiKeyInput.trim()) return;
    try {
      const res = await saveApiKey(apiKeyInput.trim());
      if (res.success) {
        onKeyStatusChange(res.has_key);
        setApiKeyInput('');
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 2000);
      }
    } catch {
    }
  };

  const handleTestKey = async () => {
    setTestingKey(true);
    setKeyTestResult(null);
    try {
      const res = await testApiKey(apiKeyInput.trim());
      setKeyTestResult({ ok: res.success, msg: res.message });
    } catch (e: any) {
      setKeyTestResult({ ok: false, msg: e.message });
    } finally {
      setTestingKey(false);
    }
  };

  const handleSavePipeline = async () => {
    try {
      const res = await updateConfig({
        transcription: {
          model: whisperModel,
          preview_enabled: previewEnabled,
        },
        format: {
          tier: tierChoice,
          groq_model: groqModel,
          ollama_model: ollamaModel,
        },
      });
      if (res.success) {
        onConfigChange(res.config);
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 2000);
      }
    } catch {
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">AI Models & Pipeline</h2>
          <p className="text-sm text-slate-400">
            Configure local speech recognition (Faster-Whisper, Vosk) and cloud cleanup failover (Groq, Ollama).
          </p>
        </div>

        {savedSuccess && (
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold animate-fadeIn">
            <Check className="w-4 h-4" />
            <span>Settings Saved</span>
          </div>
        )}
      </div>

      <div className="p-6 rounded-2xl glass-panel border border-white/5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              <Key className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Groq Cloud API Key (Tier 1 Speed)</h3>
              <p className="text-xs text-slate-400">Stored safely in your OS Keychain (Windows Credential Manager). Never stored in plaintext.</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className={`w-2.5 h-2.5 rounded-full ${hasKey ? 'bg-emerald-400' : 'bg-slate-500'}`} />
            <span className="text-xs font-mono font-medium text-slate-300">
              {hasKey ? 'Keychain Key Configured' : 'No Key Set (Using Local Fallback)'}
            </span>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-3">
          <input
            type="password"
            placeholder={hasKey ? '••••••••••••••••••••••••••••••••' : 'Enter gsk_... key from console.groq.com'}
            value={apiKeyInput}
            onChange={(e) => setApiKeyInput(e.target.value)}
            className="flex-1 px-4 py-2.5 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-indigo-500"
          />

          <div className="flex space-x-2">
            <button
              onClick={handleTestKey}
              disabled={testingKey || !apiKeyInput.trim()}
              className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-white/10 hover:bg-white/5 text-slate-300 text-xs font-semibold flex items-center space-x-1.5 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${testingKey ? 'animate-spin' : ''}`} />
              <span>Test Key</span>
            </button>

            <button
              onClick={handleSaveKey}
              disabled={!apiKeyInput.trim()}
              className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-lg shadow-indigo-600/20 disabled:opacity-50"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Save to Keychain</span>
            </button>
          </div>
        </div>

        {keyTestResult && (
          <div className={`p-3 rounded-xl border text-xs font-medium flex items-center space-x-2 ${
            keyTestResult.ok
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}>
            {keyTestResult.ok ? <Check className="w-4 h-4 text-emerald-400" /> : <AlertCircle className="w-4 h-4 text-rose-400" />}
            <span>{keyTestResult.msg}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl glass-panel border border-white/5 space-y-4">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">Local Speech Recognition (Whisper)</h3>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 font-medium block mb-1.5">Faster-Whisper Model Size</label>
              <select
                value={whisperModel}
                onChange={(e) => setWhisperModel(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-medium focus:outline-none focus:border-indigo-500"
              >
                <option value="tiny">Tiny (~75 MB, ~80ms latency)</option>
                <option value="base">Base (~145 MB, Balanced — Default)</option>
                <option value="small">Small (~460 MB, High Accuracy)</option>
                <option value="medium">Medium (~1.5 GB, Studio Quality)</option>
              </select>
            </div>

            <div className="flex items-center justify-between pt-2">
              <div>
                <div className="text-xs font-medium text-white">Streaming Live Preview (Vosk)</div>
                <div className="text-[11px] text-slate-400">Stream words in real-time as you hold the hotkey.</div>
              </div>
              <input
                type="checkbox"
                checked={previewEnabled}
                onChange={(e) => setPreviewEnabled(e.target.checked)}
                className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-white/20 focus:ring-indigo-500 focus:ring-offset-0"
              />
            </div>
          </div>
        </div>

        <div className="p-6 rounded-2xl glass-panel border border-white/5 space-y-4">
          <div className="flex items-center space-x-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">3-Tier Cleanup Failover</h3>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 font-medium block mb-1.5">Cleanup Pipeline Routing</label>
              <select
                value={tierChoice}
                onChange={(e) => setTierChoice(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-medium focus:outline-none focus:border-indigo-500"
              >
                <option value="auto">Automatic (Groq Cloud → Ollama Local → Offline Rules)</option>
                <option value="groq">Force Groq Cloud Only</option>
                <option value="ollama">Force Ollama Local Only</option>
                <option value="rule">Force Deterministic Offline Rules (Zero LLM)</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-slate-400 font-medium block mb-1.5">Groq Model Target</label>
              <input
                type="text"
                value={groqModel}
                onChange={(e) => setGroqModel(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 font-medium block mb-1.5">Local Ollama Model</label>
              <input
                type="text"
                value={ollamaModel}
                onChange={(e) => setOllamaModel(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleSavePipeline}
          className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-lg shadow-indigo-600/20"
        >
          <Check className="w-3.5 h-3.5" />
          <span>Save Pipeline Changes</span>
        </button>
      </div>
    </div>
  );
};
