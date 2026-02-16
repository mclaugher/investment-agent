import { create } from "zustand";
import type { AgentSummary, AgentDetail } from "../types";
import {
  fetchAgents as apiFetchAgents,
  fetchAgentDetail as apiFetchAgentDetail,
} from "../lib/api";

interface AgentState {
  agents: AgentSummary[];
  selectedAgent: AgentDetail | null;
  loading: boolean;
  fetchAgents: () => Promise<void>;
  fetchAgentDetail: (name: string) => Promise<void>;
  updateAgentStatus: (name: string, status: string) => void;
}

export const useAgentStore = create<AgentState>()((set, get) => ({
  agents: [],
  selectedAgent: null,
  loading: false,

  fetchAgents: async () => {
    set({ loading: true });
    try {
      const agents = await apiFetchAgents();
      set({ agents, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchAgentDetail: async (name: string) => {
    set({ loading: true });
    try {
      const detail = await apiFetchAgentDetail(name);
      set({ selectedAgent: detail, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  updateAgentStatus: (name: string, status: string) => {
    const { agents, selectedAgent } = get();
    const updated = agents.map((a) =>
      a.name === name ? { ...a, status } : a
    );
    set({
      agents: updated,
      selectedAgent:
        selectedAgent?.name === name
          ? { ...selectedAgent, status }
          : selectedAgent,
    });
  },
}));
