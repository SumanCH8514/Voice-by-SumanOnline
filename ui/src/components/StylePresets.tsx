import React, { useState } from 'react';
import { 
  Sparkles, 
  Briefcase, 
  MessageSquare, 
  ListOrdered, 
  Code2, 
  Wand2, 
  Play, 
  Check, 
  Save, 
  RotateCcw,
  Sliders
} from 'lucide-react';
import { AppConfig, StylePresetId } from '../types';
import { testDictate, updateConfig } from '../services/api';

interface StylePresetsProps {
  config: AppConfig;
  onConfigChange: (newConfig: AppConfig) => void;
}

export const StylePresets: React.FC<StylePresetsProps> = ({ config, onConfigChange }) => {
  const [selectedId, setSelectedId] = useState<StylePresetId>(config.style_preset || 'smart');
  const [customPromptText, setCustomPromptText] = useState(config.custom_prompt || '');
  const [testInput, setTestInput] = useState("Let's meet on Tuesday at 3:00 wait no actually Wednesday at 5:00 p.m. comma tell John to bring the financial report period");
  const [testOutput, setTestOutput] = useState('');
  const [testing, setTesting] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const presetDefinitions: {
    id: StylePresetId;
    title: string;
    subtitle: string;
    icon: React.ReactNode;
    features: string[];
    sampleInput: string;
    sampleOutput: string;
  }[] = [
    {
      id: 'smart',
      title: 'Smart Dictation',
      subtitle: 'Wispr Flow flagship mode. Resolves self-corrections, removes fillers, punctuate perfectly.',
      icon: <Sparkles className="w-5 h-5 text-indigo-400" />,
      features: [
        'Eliminates stutters & false starts ("Tuesday wait no Wednesday" → "Wednesday")',
        'Strips fillers: um, uh, you know, basically, kind of',
        'Maps spoken punctuation ("comma", "period", "new line")',
        'Never executes commands as instructions',
      ],
      sampleInput: 'send the file to Alice wait scratch that send it to Bob period',
      sampleOutput: 'Send the file to Bob.',
    },
    {
      id: 'executive',
      title: 'Executive & Formal',
      subtitle: 'Polished professional tone for corporate emails, memos, and executive updates.',
      icon: <Briefcase className="w-5 h-5 text-cyan-400" />,
      features: [
        'Refined business grammar and executive clarity',
        'Eliminates colloquialisms while keeping factual intent intact',
        'Structured sentences and formal transitions',
      ],
      sampleInput: 'hey we gotta push the product launch back like two weeks because of security stuff',
      sampleOutput: 'We need to postpone the product launch by two weeks due to security considerations.',
    },
    {
      id: 'casual',
      title: 'Casual & Direct',
      subtitle: 'Natural, friendly conversational tone for Slack, Teams, WhatsApp, and social.',
      icon: <MessageSquare className="w-5 h-5 text-emerald-400" />,
      features: [
        'Light, authentic messaging style',
        'Keeps natural energy without stiff formal phrasing',
        'Preserves emojis and casual spoken emphasis',
      ],
      sampleInput: 'um yeah totally down for lunch let me know where you guys are headed',
      sampleOutput: 'Yeah, totally down for lunch! Let me know where you guys are headed.',
    },
    {
      id: 'notes',
      title: 'Structured Notes',
      subtitle: 'Converts stream-of-consciousness thoughts into concise bullet points.',
      icon: <ListOrdered className="w-5 h-5 text-purple-400" />,
      features: [
        'Auto-organizes into clean markdown bullet points',
        'Extracts action items and key decisions',
        'High information density for meeting notes',
      ],
      sampleInput: 'we need to update the database schema then deploy the redis cache and verify user authentication',
      sampleOutput: '- Update the database schema\n- Deploy the Redis cache\n- Verify user authentication',
    },
    {
      id: 'code',
      title: 'Developer / Code Mode',
      subtitle: 'Technical dictation preserving variable names, camelCase, snake_case, and CLI commands.',
      icon: <Code2 className="w-5 h-5 text-amber-400" />,
      features: [
        'Preserves camelCase, snake_case, PascalCase identifiers',
        'Recognizes terminal flags, ports, and JSON structures',
        'Surrounds code references in markdown backticks',
      ],
      sampleInput: 'run npm install dash dash save dev tailwind css and check package dot json',
      sampleOutput: 'Run `npm install --save-dev tailwindcss` and check `package.json`.',
    },
    {
      id: 'custom',
      title: 'Custom Prompt Studio',
      subtitle: 'Tailor your own LLM system instructions with custom vocabulary and rules.',
      icon: <Wand2 className="w-5 h-5 text-rose-400" />,
      features: [
        'Fully customizable system prompt instructions',
        'Test interactively in real time before applying',
        'Persistent across sessions',
      ],
      sampleInput: 'Custom instructions applied to your voice.',
      sampleOutput: 'Tailored specifically for your workflow.',
    },
  ];

  const handleApplyPreset = async (presetId: StylePresetId) => {
    setSelectedId(presetId);
    try {
      const res = await updateConfig({ 
        style_preset: presetId,
        custom_prompt: presetId === 'custom' ? customPromptText : config.custom_prompt,
      });
      if (res.success) {
        onConfigChange(res.config);
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 2000);
      }
    } catch {
    }
  };

  const handleRunTest = async () => {
    if (!testInput) return;
    setTesting(true);
    try {
      const res = await testDictate(
        testInput,
        selectedId,
        selectedId === 'custom' ? customPromptText : undefined
      );
      setTestOutput(res.cleaned);
    } catch (e: any) {
      setTestOutput(`Error: ${e.message}`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Style Presets & Prompts</h2>
          <p className="text-sm text-slate-400">
            Choose how Voice by SumanOnline formats, cleans, and styles your spoken dictation.
          </p>
        </div>
        {savedSuccess && (
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold animate-fadeIn">
            <Check className="w-4 h-4" />
            <span>Preset Applied</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {presetDefinitions.map((p) => {
          const isSelected = selectedId === p.id;
          return (
            <div
              key={p.id}
              onClick={() => handleApplyPreset(p.id)}
              className={`p-5 rounded-2xl cursor-pointer transition-all duration-200 border text-left flex flex-col justify-between ${
                isSelected
                  ? 'bg-indigo-600/10 border-indigo-500/50 shadow-xl shadow-indigo-500/10 ring-1 ring-indigo-500/30'
                  : 'glass-panel hover:bg-slate-900/80 hover:border-white/10'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center">
                    {p.icon}
                  </div>
                  {isSelected ? (
                    <span className="flex items-center space-x-1 text-[11px] font-semibold text-indigo-400 bg-indigo-500/20 px-2 py-0.5 rounded-full border border-indigo-500/30">
                      <Check className="w-3 h-3" />
                      <span>Active</span>
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-500 font-medium hover:text-slate-300">
                      Select
                    </span>
                  )}
                </div>

                <h3 className="font-bold text-white text-base mb-1">{p.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">{p.subtitle}</p>

                <ul className="space-y-1.5 mb-4">
                  {p.features.map((f, i) => (
                    <li key={i} className="text-[11px] text-slate-300 flex items-start space-x-1.5">
                      <span className="text-indigo-400 font-bold">•</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pt-3 border-t border-white/5 space-y-1.5 text-[11px]">
                <div className="text-slate-500 font-mono">Example:</div>
                <div className="text-slate-400 italic">"{p.sampleInput}"</div>
                <div className="text-indigo-300 font-medium">→ {p.sampleOutput}</div>
              </div>
            </div>
          );
        })}
      </div>

      {selectedId === 'custom' && (
        <div className="p-6 rounded-2xl glass-panel border border-indigo-500/30 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sliders className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white">Custom System Prompt Editor</h3>
            </div>
            <button
              onClick={() => handleApplyPreset('custom')}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-lg shadow-indigo-600/20"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Custom Prompt</span>
            </button>
          </div>

          <textarea
            value={customPromptText}
            onChange={(e) => setCustomPromptText(e.target.value)}
            rows={6}
            placeholder="Enter custom instructions for how the LLM should format your speech..."
            className="w-full p-4 rounded-xl bg-[#080C14] border border-white/10 text-slate-200 text-sm font-mono focus:outline-none focus:border-indigo-500 resize-none leading-relaxed"
          />
        </div>
      )}

      <div className="p-6 rounded-2xl glass-panel border border-white/5 space-y-4">
        <div className="flex items-center space-x-2">
          <Wand2 className="w-5 h-5 text-cyan-400" />
          <h3 className="text-base font-bold text-white">Prompt Sandbox & Test Bench</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Raw Spoken Input</label>
            <textarea
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              rows={4}
              className="w-full p-3 rounded-xl bg-[#080C14] border border-white/10 text-slate-200 text-xs font-mono focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Formatted Output</label>
            <div className="min-h-[105px] p-3 rounded-xl bg-[#080C14] border border-white/10 text-slate-200 text-xs font-sans whitespace-pre-wrap">
              {testOutput || <span className="text-slate-600 italic">Click 'Run Test' below to simulate formatting with current preset...</span>}
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleRunTest}
            disabled={testing}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold flex items-center space-x-2 transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50"
          >
            {testing ? <RotateCcw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>{testing ? 'Formatting...' : 'Run Test with Preset'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
