import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AgentId } from "../api/types";

interface SettingsState {
  agent: AgentId;
  provider: string;
  model: string;
  temperature: number;
  /** Stored in this browser's localStorage only and sent per request. Never persisted by the server. */
  apiKeys: Record<string, string>;
  requireApproval: boolean;
  /** null = every tool enabled */
  enabledTools: string[] | null;
  systemPrompt: string;
  patch: (p: Partial<Omit<SettingsState, "patch" | "setApiKey">>) => void;
  setApiKey: (provider: string, key: string) => void;
}

export const useSettings = create<SettingsState>()(
  persist(
    (set) => ({
      agent: "assistant",
      provider: "openai",
      model: "gpt-4o-mini",
      temperature: 0.2,
      apiKeys: {},
      requireApproval: true,
      enabledTools: null,
      systemPrompt: "",
      patch: (p) => set(p),
      setApiKey: (provider, key) => set((s) => ({ apiKeys: { ...s.apiKeys, [provider]: key } })),
    }),
    { name: "ai-workbench-settings" },
  ),
);
