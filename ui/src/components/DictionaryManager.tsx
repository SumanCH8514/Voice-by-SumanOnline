import React, { useState } from 'react';
import { 
  BookA, 
  Plus, 
  Trash2, 
  Search, 
  Download, 
  Upload, 
  Save, 
  Check, 
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { AppConfig } from '../types';
import { saveDictionary } from '../services/api';

interface DictionaryManagerProps {
  config: AppConfig;
  onConfigChange: (newConfig: AppConfig) => void;
}

export const DictionaryManager: React.FC<DictionaryManagerProps> = ({ config, onConfigChange }) => {
  const [pairs, setPairs] = useState<[string, string][]>(config.dictionary || []);
  const [searchTerm, setSearchTerm] = useState('');
  const [findText, setFindText] = useState('');
  const [replaceText, setReplaceText] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleAdd = () => {
    if (!findText.trim() || !replaceText.trim()) return;
    const updated: [string, string][] = [...pairs, [findText.trim(), replaceText.trim()]];
    setPairs(updated);
    setFindText('');
    setReplaceText('');
    persistDictionary(updated);
  };

  const handleRemove = (index: number) => {
    const updated = pairs.filter((_, i) => i !== index);
    setPairs(updated);
    persistDictionary(updated);
  };

  const persistDictionary = async (updated: [string, string][]) => {
    try {
      await saveDictionary(updated);
      onConfigChange({ ...config, dictionary: updated });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2000);
    } catch {
    }
  };

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(pairs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'voice-dictionary.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const parsed = JSON.parse(evt.target?.result as string);
        if (Array.isArray(parsed)) {
          setPairs(parsed);
          persistDictionary(parsed);
        }
      } catch {
      }
    };
    reader.readAsText(file);
  };

  const filtered = pairs.filter(
    ([f, r]) =>
      f.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Personal Dictionary</h2>
          <p className="text-sm text-slate-400">
            Case-insensitive, word-boundary safe replacements applied immediately after transcription.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <label className="px-3 py-2 rounded-xl bg-slate-900 border border-white/10 hover:bg-white/5 text-slate-300 text-xs font-semibold flex items-center space-x-1.5 cursor-pointer transition-colors">
            <Upload className="w-3.5 h-3.5" />
            <span>Import JSON</span>
            <input type="file" accept=".json" onChange={handleImport} className="hidden" />
          </label>

          <button
            onClick={handleExport}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-white/10 hover:bg-white/5 text-slate-300 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export</span>
          </button>
        </div>
      </div>

      <div className="p-6 rounded-2xl glass-panel border border-white/5 space-y-4">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Add Replacement Rule</h3>
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 items-center">
          <div className="md:col-span-3">
            <input
              type="text"
              placeholder="Spoken words (e.g. 'suman online')"
              value={findText}
              onChange={(e) => setFindText(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-medium focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="hidden md:flex justify-center text-slate-500">
            <ArrowRight className="w-4 h-4" />
          </div>

          <div className="md:col-span-2">
            <input
              type="text"
              placeholder="Replace with (e.g. 'SumanOnline')"
              value={replaceText}
              onChange={(e) => setReplaceText(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#080C14] border border-white/10 text-white text-xs font-medium focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            onClick={handleAdd}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors shadow-lg shadow-indigo-600/20"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Rule</span>
          </button>
        </div>
      </div>

      <div className="rounded-2xl glass-panel border border-white/5 overflow-hidden">
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <div className="relative w-72">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search vocabulary..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-[#080C14] border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="text-xs text-slate-400 font-medium">
            {pairs.length} {pairs.length === 1 ? 'rule' : 'rules'} registered
          </div>
        </div>

        <div className="divide-y divide-white/5 max-h-[380px] overflow-y-auto">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs">
              No dictionary rules match your search.
            </div>
          ) : (
            filtered.map(([find, replace], idx) => (
              <div
                key={idx}
                className="p-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-2 h-2 rounded-full bg-indigo-500/50" />
                  <span className="font-mono text-xs text-slate-300 font-medium">{find}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                  <span className="font-mono text-xs text-indigo-400 font-semibold bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    {replace}
                  </span>
                </div>

                <button
                  onClick={() => handleRemove(idx)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  title="Remove rule"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
