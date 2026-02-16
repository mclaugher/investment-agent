import { useEffect, useState } from "react";
import { useAgentStore } from "@/store/agentStore";
import { AgentTree } from "@/components/agents/AgentTree";
import { AgentDetail } from "@/components/agents/AgentDetail";
import type { AgentDetail as AgentDetailType } from "@/types";

export default function Agents() {
  const agents = useAgentStore((s) => s.agents);
  const agentDetail = useAgentStore((s) => s.selectedAgent);
  const fetchAgents = useAgentStore((s) => s.fetchAgents);
  const fetchAgentDetail = useAgentStore((s) => s.fetchAgentDetail);

  const [selectedName, setSelectedName] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  useEffect(() => {
    if (selectedName) {
      fetchAgentDetail(selectedName);
    }
  }, [selectedName, fetchAgentDetail]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
        <p className="text-sm text-gray-500 mt-1">
          Multi-agent hierarchy and activity
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <AgentTree
            agents={agents}
            selectedAgent={selectedName}
            onSelect={setSelectedName}
          />
        </div>
        <div className="lg:col-span-2">
          {agentDetail ? (
            <AgentDetail agent={agentDetail} />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <p className="text-sm text-gray-500">
                Select an agent from the hierarchy to view details.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
