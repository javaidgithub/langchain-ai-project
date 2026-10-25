import { create } from "zustand";
import { api } from "../api/client";
import type { AgentInfo, ProviderInfo, ToolInfo } from "../api/types";

interface CatalogState {
  providers: ProviderInfo[];
  tools: ToolInfo[];
  agents: AgentInfo[];
  backendError: string | null;
  load: () => Promise<void>;
}

export const useCatalog = create<CatalogState>((set) => ({
  providers: [],
  tools: [],
  agents: [],
  backendError: null,
  load: async () => {
    try {
      const [providers, tools, agents] = await Promise.all([api.models(), api.tools(), api.agents()]);
      set({ providers, tools, agents, backendError: null });
    } catch (err) {
      set({ backendError: (err as Error).message });
    }
  },
}));
