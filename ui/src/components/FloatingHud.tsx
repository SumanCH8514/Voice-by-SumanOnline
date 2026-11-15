import React, { useEffect, useRef } from 'react';
import { Mic, Loader2, Sparkles, Check } from 'lucide-react';
import { StylePresetId } from '../types';

interface FloatingHudProps {
  isRecording: boolean;
  isProcessing: boolean;
  rms: number;
  rmsBars: number[];
  previewText: string;
  statusText: string;
  stylePreset: StylePresetId;
  onFinish?: () => void;
}

export const FloatingHud: React.FC<FloatingHudProps> = ({
  isRecording,
  isProcessing,
  rms,
  previewText,
  statusText,
  stylePreset,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const pulseRef = useRef(0);

  useEffect(() => {
    let animId: number;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const render = () => {
      pulseRef.current += 0.05;
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const midY = h / 2;
      const points = 32;
      const step = w / points;

      ctx.beginPath();
      ctx.moveTo(0, midY);

      for (let i = 0; i <= points; i++) {
        const x = i * step;
        const norm = i / points;
        const env = Math.sin(norm * Math.PI);
        const amp = isRecording ? Math.max(0.1, rms * 40) : isProcessing ? 6 : 2;
        const freq1 = Math.sin(pulseRef.current * 3 + norm * 8) * amp;
        const freq2 = Math.cos(pulseRef.current * 2 + norm * 5) * (amp * 0.5);
        const y = midY + env * (freq1 + freq2);
        ctx.lineTo(x, y);
      }

      ctx.strokeStyle = isRecording
        ? 'rgba(99, 102, 241, 0.9)'
        : isProcessing
        ? 'rgba(245, 158, 11, 0.9)'
        : 'rgba(100, 116, 139, 0.4)';
      ctx.lineWidth = 2.5;
      ctx.lineCap = 'round';
      ctx.shadowColor = isRecording ? '#6366F1' : isProcessing ? '#F59E0B' : 'transparent';
      ctx.shadowBlur = 12;
      ctx.stroke();

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [isRecording, isProcessing, rms]);

  const styleLabels: Record<StylePresetId, string> = {
    smart: 'Smart Dictation',
    executive: 'Executive',
    casual: 'Casual',
    notes: 'Structured Notes',
    code: 'Developer',
    custom: 'Custom',
  };

  return (
    <div className="glass-pill px-5 py-3 rounded-2xl flex flex-col space-y-2 select-none min-w-[340px] max-w-md transition-all duration-200">
      <div className="flex items-center justify-between space-x-3">
        <div className="flex items-center space-x-2.5">
          <div className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
            isRecording
              ? 'bg-indigo-600/30 text-indigo-400 ring-2 ring-indigo-500/50 animate-pulse'
              : isProcessing
              ? 'bg-amber-500/20 text-amber-400 ring-2 ring-amber-500/30'
              : 'bg-white/5 text-slate-400'
          }`}>
            {isRecording ? (
              <Mic className="w-4 h-4 text-indigo-400" />
            ) : isProcessing ? (
              <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
            ) : (
              <Check className="w-4 h-4 text-emerald-400" />
            )}
          </div>
          <div>
            <div className="text-xs font-semibold text-white tracking-wide flex items-center space-x-1.5">
              <span>{isRecording ? 'Listening...' : isProcessing ? 'Polishing Transcript...' : 'Ready'}</span>
              <span className="text-[10px] text-slate-400 font-normal">({styleLabels[stylePreset]})</span>
            </div>
          </div>
        </div>

        <div className="w-28 h-6 relative overflow-hidden rounded">
          <canvas
            ref={canvasRef}
            width={112}
            height={24}
            className="w-full h-full block"
          />
        </div>
      </div>

      {(previewText || statusText) && (
        <div className="pt-2 border-t border-white/10 text-xs text-slate-300 font-medium truncate flex items-center space-x-1.5">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <span className="truncate">{previewText || statusText}</span>
        </div>
      )}
    </div>
  );
};
