import React, { useState, useEffect } from 'react';
import { 
  History, 
  Trash2, 
  Search, 
  Copy, 
  Check, 
  Clock, 
  Flame, 
  Sparkles, 
  Zap, 
  Timer,
  FileText
} from 'lucide-react';
import { HistoryEntry, StatsSummary } from '../types';
import { clearHistory, fetchHistory } from '../services/api';

export const HistoryAnalytics: React.FC = () => {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [stats, setStats] = useState<StatsSummary>({
    total_dictations: 0,
    total_words: 0,
    total_audio_seconds: 0,
    estimated_minutes_saved: 0,
    recent_count: 0,
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const res = await fetchHistory();
      setHistory(res.history);
      setStats(res.stats);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClear = async () => {
    if (!window.confirm('Clear all dictation history? This cannot be undone.')) return;
    try {
      await clearHistory();
      setHistory([]);
      setStats({
        total_dictations: 0,
        total_words: 0,
        total_audio_seconds: 0,
        estimated_minutes_saved: 0,
        recent_count: 0,
      });
    } catch {
    }
  };

  const filtered = history.filter(
    (h) =>
      h.cleaned_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
      h.raw_text.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">History & Productivity Analytics</h2>
          <p className="text-sm text-slate-400">
            Review past voice transcripts and measure hours saved compared to typing.
          </p>
        </div>

        {history.length > 0 && (
          <button
            onClick={handleClear}
            className="px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-colors self-start md:self-auto"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Time Saved</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400">
              <Timer className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {stats.estimated_minutes_saved > 60
              ? `${(stats.estimated_minutes_saved / 60).toFixed(1)} hrs`
              : `${stats.estimated_minutes_saved} min`}
          </div>
          <p className="text-[11px] text-slate-500">Based on 150 wpm speech vs 40 wpm typing</p>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Words</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {stats.total_words.toLocaleString()}
          </div>
          <p className="text-[11px] text-slate-500">Across all dictation sessions</p>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Dictations</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {stats.total_dictations.toLocaleString()}
          </div>
          <p className="text-[11px] text-slate-500">Total push-to-talk triggers</p>
        </div>

        <div className="p-5 rounded-2xl glass-panel border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Spoken Audio</span>
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {stats.total_audio_seconds > 60
              ? `${(stats.total_audio_seconds / 60).toFixed(1)} min`
              : `${stats.total_audio_seconds}s`}
          </div>
          <p className="text-[11px] text-slate-500">Total microphone recording time</p>
        </div>
      </div>

      <div className="rounded-2xl glass-panel border border-white/5 overflow-hidden">
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <div className="relative w-80">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search transcript history..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-[#080C14] border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div className="text-xs text-slate-400 font-medium">
            {filtered.length} entries
          </div>
        </div>

        <div className="divide-y divide-white/5 max-h-[480px] overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No dictations recorded yet. Hold your hotkey to dictate anywhere!
            </div>
          ) : (
            filtered.map((item) => (
              <div key={item.id} className="p-5 hover:bg-white/[0.02] transition-colors space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {item.preset || 'smart'}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-xs text-slate-400 font-mono">{item.word_count} words</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-xs text-slate-400 font-mono">{item.latency_s}s</span>
                  </div>

                  <button
                    onClick={() => handleCopy(item.id, item.cleaned_text)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors flex items-center space-x-1 text-xs"
                    title="Copy text"
                  >
                    {copiedId === item.id ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span>{copiedId === item.id ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>

                <div className="text-sm text-slate-100 font-sans leading-relaxed select-text">
                  {item.cleaned_text}
                </div>

                {item.raw_text !== item.cleaned_text && (
                  <div className="text-xs text-slate-500 font-mono italic">
                    Raw: "{item.raw_text}"
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
