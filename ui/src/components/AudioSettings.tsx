import React, { useState, useEffect } from 'react';
import { 
  Volume2, 
  Mic, 
  Activity, 
  ShieldCheck, 
  RefreshCw, 
  Check, 
  Radio, 
  SlidersHorizontal 
} from 'lucide-react';
import { AppConfig, AudioDevice } from '../types';
import { fetchDevices, updateConfig } from '../services/api';

interface AudioSettingsProps {
  config: AppConfig;
  rms: number;
  onConfigChange: (newConfig: AppConfig) => void;
}

export const AudioSettings: React.FC<AudioSettingsProps> = ({ config, rms, onConfigChange }) => {
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<any>(config.input_device);
  const [loading, setLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const loadDevices = async () => {
    setLoading(true);
    try {
      const res = await fetchDevices();
      setDevices(res.devices);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDevices();
  }, []);

  const handleDeviceChange = async (val: string) => {
    const parsed = val === 'auto' ? null : isNaN(Number(val)) ? val : Number(val);
    setSelectedDevice(parsed);
    try {
      const res = await updateConfig({ input_device: parsed });
      if (res.success) {
        onConfigChange(res.config);
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 2000);
      }
    } catch {
    }
  };

  const dbLevel = Math.min(100, Math.round(rms * 400));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Audio & Microphone</h2>
          <p className="text-sm text-slate-400">
            Hardware input routing, stereo downmixing, and resilience against wireless disconnects.
          </p>
        </div>

        <button
          onClick={loadDevices}
          disabled={loading}
          className="px-3 py-2 rounded-xl bg-slate-900 border border-white/10 hover:bg-white/5 text-slate-300 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Devices</span>
        </button>
      </div>

      <div className="p-6 rounded-2xl glass-panel border border-white/5 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              <Mic className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Default Microphone Input</h3>
              <p className="text-xs text-slate-400">Lock the audio recorder to a specific hardware input.</p>
            </div>
          </div>

          {savedSuccess && (
            <span className="text-xs text-emerald-400 font-semibold flex items-center space-x-1">
              <Check className="w-3.5 h-3.5" />
              <span>Saved</span>
            </span>
          )}
        </div>

        <div>
          <select
            value={selectedDevice === null ? 'auto' : String(selectedDevice)}
            onChange={(e) => handleDeviceChange(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-medium focus:outline-none focus:border-indigo-500"
          >
            <option value="auto">System Default (Automatic Fallback)</option>
            {devices.map((d) => (
              <option key={d.index} value={String(d.index)}>
                #{d.index}: {d.name} ({d.sample_rate} Hz, {d.channels} ch)
              </option>
            ))}
          </select>
        </div>

        <div className="p-4 rounded-xl bg-[#080C14] border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium flex items-center space-x-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              <span>Live Microphone Activity</span>
            </span>
            <span className="font-mono text-indigo-400 font-bold">{dbLevel}%</span>
          </div>

          <div className="w-full h-3 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-white/5">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 rounded-full transition-all duration-75"
              style={{ width: `${dbLevel}%` }}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-3">
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-cyan-400" />
            <h4 className="text-sm font-bold text-white">Polyphase Resampling Engine</h4>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Mics are opened at their native sample rate (44.1 kHz, 48 kHz, or 96 kHz) and downmixed to 16 kHz mono using <code className="text-indigo-300 font-mono">scipy.signal.resample_poly</code> to prevent channel clipping.
          </p>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h4 className="text-sm font-bold text-white">Dead Wireless Silence Detection</h4>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            If 1.5 seconds of 100% digital silence is detected (e.g., DJI Mic or wireless headset dongle turned off), PortAudio auto-reinitializes and falls back to the built-in microphone seamlessly.
          </p>
        </div>
      </div>
    </div>
  );
};
