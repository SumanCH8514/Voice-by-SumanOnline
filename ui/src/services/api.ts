import { AppConfig, AppStatus, AudioDevice, HistoryEntry, StatsSummary } from '../types';

const BASE_URL = '';

export async function fetchStatus(): Promise<AppStatus> {
  const res = await fetch(`${BASE_URL}/api/status`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchConfig(): Promise<AppConfig> {
  const res = await fetch(`${BASE_URL}/api/config`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function updateConfig(updates: Partial<AppConfig>): Promise<{ success: boolean; config: AppConfig }> {
  const res = await fetch(`${BASE_URL}/api/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchDevices(): Promise<{ devices: AudioDevice[]; default_index: number | null }> {
  const res = await fetch(`${BASE_URL}/api/devices`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchHistory(): Promise<{ history: HistoryEntry[]; stats: StatsSummary }> {
  const res = await fetch(`${BASE_URL}/api/history`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function clearHistory(): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE_URL}/api/history`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchDictionary(): Promise<{ dictionary: [string, string][] }> {
  const res = await fetch(`${BASE_URL}/api/dictionary`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function saveDictionary(dictionary: [string, string][]): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE_URL}/api/dictionary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dictionary }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function saveApiKey(apiKey: string): Promise<{ success: boolean; has_key: boolean }> {
  const res = await fetch(`${BASE_URL}/api/key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function testApiKey(apiKey: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${BASE_URL}/api/test-key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function testDictate(
  text: string,
  stylePreset: string = 'smart',
  customPrompt?: string,
  tierOverride?: string
): Promise<{
  raw: string;
  cleaned: string;
  tier: string;
  latency_s: number;
  word_count_in: number;
  word_count_out: number;
}> {
  const res = await fetch(`${BASE_URL}/api/dictate/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      style_preset: stylePreset,
      custom_prompt: customPrompt,
      tier_override: tierOverride,
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function triggerManualRecording(): Promise<{ success: boolean; state: string }> {
  const res = await fetch(`${BASE_URL}/api/toggle-recording`, { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function triggerToggleMute(): Promise<{ success: boolean; muted: boolean }> {
  const res = await fetch(`${BASE_URL}/api/toggle-mute`, { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function createLiveWebSocket(onMessage: (data: any) => void): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host || 'localhost:48922';
  const ws = new WebSocket(`${protocol}//${host}/ws/live`);
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
    }
  };
  return ws;
}
