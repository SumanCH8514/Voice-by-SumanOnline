import React from 'react';
import { 
  Mic, 
  Sparkles, 
  BookA, 
  History, 
  Volume2, 
  Cpu, 
  Keyboard, 
  Download,
  VolumeX,
  Radio
} from 'lucide-react';
import { TabType } from '../types';

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  isRecording: boolean;
  isProcessing: boolean;
  isMuted: boolean;
  onToggleMute: () => void;
  onToggleRecording: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isRecording,
  isProcessing,
  isMuted,
  onToggleMute,
  onToggleRecording,
}) => {
  const menuItems: { id: TabType; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'studio', label: 'Voice Studio', icon: <Mic className="w-5 h-5" /> },
    { id: 'presets', label: 'Style Presets', icon: <Sparkles className="w-5 h-5" /> },
    { id: 'dictionary', label: 'Dictionary', icon: <BookA className="w-5 h-5" /> },
    { id: 'history', label: 'History & Stats', icon: <History className="w-5 h-5" /> },
    { id: 'audio', label: 'Audio & Mic', icon: <Volume2 className="w-5 h-5" /> },
    { id: 'engine', label: 'AI Models', icon: <Cpu className="w-5 h-5" /> },
    { id: 'shortcuts', label: 'Shortcuts', icon: <Keyboard className="w-5 h-5" /> },
    { id: 'install', label: 'Install App', icon: <Download className="w-5 h-5" />, badge: 'Setup' },
  ];

  return (
    <aside className="w-64 bg-[#0B0F19] border-r border-white/5 flex flex-col justify-between select-none">
      <div>
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl overflow-hidden shadow-lg shadow-indigo-500/25 border border-indigo-500/30 flex-shrink-0">
              <img src="/logo.png" alt="Voice by SumanOnline" className="w-full h-full object-cover" />
            </div>
            <div>
              <h1 className="font-semibold text-white tracking-tight leading-none text-base">
                Voice
              </h1>
              <span className="text-[11px] font-medium text-indigo-400 tracking-wider uppercase">
                by SumanOnline
              </span>
            </div>
          </div>
        </div>

        <nav className="p-3 space-y-1">
          {menuItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-indigo-600/15 text-white border border-indigo-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className={isActive ? 'text-indigo-400' : 'text-slate-400'}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-white/5 space-y-3">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Quick Push-to-Talk</span>
            <div className="flex items-center space-x-1.5">
              <span className={`w-2 h-2 rounded-full ${isRecording ? 'bg-emerald-500 animate-ping' : isProcessing ? 'bg-amber-500 animate-pulse' : 'bg-slate-600'}`} />
              <span className="text-[11px] text-slate-400 font-mono">
                {isRecording ? 'Recording' : isProcessing ? 'Transcribing' : 'Ready'}
              </span>
            </div>
          </div>
          <button
            onClick={onToggleRecording}
            className={`w-full py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${
              isRecording
                ? 'bg-rose-500 hover:bg-rose-600 text-white shadow-lg shadow-rose-500/20'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20'
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            <span>{isRecording ? 'Finish & Inject' : 'Dictate Test'}</span>
          </button>
        </div>

        <button
          onClick={onToggleMute}
          className={`w-full py-2 px-3 rounded-xl border text-xs font-medium flex items-center justify-center space-x-2 transition-colors ${
            isMuted
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20'
              : 'bg-white/[0.02] border-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/[0.05]'
          }`}
        >
          {isMuted ? <VolumeX className="w-3.5 h-3.5 text-amber-400" /> : <Volume2 className="w-3.5 h-3.5" />}
          <span>{isMuted ? 'Muted (Click to Unmute)' : 'Active (Click to Mute)'}</span>
        </button>
      </div>
    </aside>
  );
};
