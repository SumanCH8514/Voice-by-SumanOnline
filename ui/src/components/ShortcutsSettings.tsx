import React, { useState } from 'react';
import { 
  Keyboard, 
  ToggleLeft, 
  Eye, 
  Monitor, 
  Check, 
  ShieldAlert, 
  HelpCircle 
} from 'lucide-react';
import { AppConfig } from '../types';
import { updateConfig } from '../services/api';

interface ShortcutsSettingsProps {
  config: AppConfig;
  onConfigChange: (newConfig: AppConfig) => void;
}

export const ShortcutsSettings: React.FC<ShortcutsSettingsProps> = ({ config, onConfigChange }) => {
  const [hotkey, setHotkey] = useState(config.hotkey || 'Key.alt_r');
  const [toggleMode, setToggleMode] = useState(bool(config.toggle_mode));
  const [overlayEnabled, setOverlayEnabled] = useState(config.overlay_enabled !== false);
  const [startOnLogin, setStartOnLogin] = useState(bool(config.start_on_login));
  const [savedSuccess, setSavedSuccess] = useState(false);

  function bool(v: any): boolean {
    return v === true || v === 'true';
  }

  const hotkeyOptions = [
    { label: 'Right Alt / Option (Recommended)', value: 'Key.alt_r' },
    { label: 'Left Alt / Option', value: 'Key.alt_l' },
    { label: 'Right Control', value: 'Key.ctrl_r' },
    { label: 'Left Control', value: 'Key.ctrl_l' },
    { label: 'Right Shift', value: 'Key.shift_r' },
    { label: 'F8 Function Key', value: 'Key.f8' },
    { label: 'F2 Function Key', value: 'Key.f2' },
  ];

  const handleSave = async (updates: Partial<AppConfig>) => {
    try {
      const res = await updateConfig(updates);
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
          <h2 className="text-xl font-bold text-white tracking-tight">Shortcuts & System Behavior</h2>
          <p className="text-sm text-slate-400">
            Configure system-wide push-to-talk triggers, hands-free toggle, and floating HUD overlay.
          </p>
        </div>

        {savedSuccess && (
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold animate-fadeIn">
            <Check className="w-4 h-4" />
            <span>Updated</span>
          </div>
        )}
      </div>

      <div className="p-6 rounded-2xl glass-panel border border-white/5 space-y-6">
        <div className="space-y-3">
          <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
            <Keyboard className="w-4 h-4 text-indigo-400" />
            <span>Global Dictation Hotkey</span>
          </label>
          <select
            value={hotkey}
            onChange={(e) => {
              const val = e.target.value;
              setHotkey(val);
              handleSave({ hotkey: val });
            }}
            className="w-full px-4 py-3 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-medium focus:outline-none focus:border-indigo-500"
          >
            {hotkeyOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400">
            On Windows, Right Alt automatically detects AltGr layouts so international keyboards work without configuration.
          </p>
        </div>

        <div className="pt-4 border-t border-white/5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="text-sm font-semibold text-white flex items-center space-x-2">
                <span>Hands-Free Toggle Mode</span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30">
                  New
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Tap once to start dictating; tap again to transcribe and inject (no need to hold the key down).
              </p>
            </div>
            <input
              type="checkbox"
              checked={toggleMode}
              onChange={(e) => {
                const val = e.target.checked;
                setToggleMode(val);
                handleSave({ toggle_mode: val });
              }}
              className="w-5 h-5 rounded text-indigo-600 bg-slate-900 border-white/20 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="text-sm font-semibold text-white">Floating On-Screen HUD Overlay</div>
              <p className="text-xs text-slate-400">
                Shows the non-activating animated soundwave pill above the Windows taskbar while recording.
              </p>
            </div>
            <input
              type="checkbox"
              checked={overlayEnabled}
              onChange={(e) => {
                const val = e.target.checked;
                setOverlayEnabled(val);
                handleSave({ overlay_enabled: val });
              }}
              className="w-5 h-5 rounded text-indigo-600 bg-slate-900 border-white/20 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="text-sm font-semibold text-white">Start on Windows Login</div>
              <p className="text-xs text-slate-400">
                Automatically launch Voice by SumanOnline in your system tray when you sign in to Windows.
              </p>
            </div>
            <input
              type="checkbox"
              checked={startOnLogin}
              onChange={(e) => {
                const val = e.target.checked;
                setStartOnLogin(val);
                handleSave({ start_on_login: val });
              }}
              className="w-5 h-5 rounded text-indigo-600 bg-slate-900 border-white/20 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      <div className="p-5 rounded-2xl glass-panel border border-white/5 flex items-start space-x-3">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 leading-relaxed">
          <strong className="text-white block mb-0.5">Windows UIPI Notice:</strong>
          Windows User Interface Privilege Isolation prevents standard user processes from sending keystrokes into elevated Administrator windows. If you dictate into an elevated Administrator terminal or text editor, run Voice by SumanOnline as Administrator.
        </div>
      </div>
    </div>
  );
};
