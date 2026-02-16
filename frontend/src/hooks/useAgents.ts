import { useEffect } from "react";
import { useAgentStore } from "../store/agentStore";

/**
 * Hook that fetches all agents on mount and returns
 * the current agent store state.
 */
export function useAgents() {
  const agents = useAgentStore((s) => s.agents);
  const selectedAgent = useAgentStore((s) => s.selectedAgent);
  const loading = useAgentStore((s) => s.loading);
  const fetchAgents = useAgentStore((s) => s.fetchAgents);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return { agents, selectedAgent, loading };
}
