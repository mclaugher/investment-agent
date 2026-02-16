import { Bot, Circle } from "lucide-react";
import { cn, formatRelativeTime } from "@/lib/utils";
import { useAgentStore } from "@/store/agentStore";

export function AgentStatusGrid() {
  const agents = useAgentStore((s) => s.agents);

  const statusColor: Record<string, string> = {
    idle: "text-green-500",
    running: "text-yellow-500",
    error: "text-red-500",
  };

  if (!agents || agents.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Agent Status</h3>
        <p className="text-sm text-gray-500">No agent data available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Agent Status</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {agents.map((agent) => (
          <div
            key={agent.name}
            className="border border-gray-200 rounded-lg p-3 hover:border-blue-300 transition-colors"
          >
            <div className="flex items-center gap-2 mb-2">
              <Bot className="h-4 w-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-900 truncate">
                {agent.name}
              </span>
            </div>
            <div className="flex items-center gap-1.5 mb-1">
              <Circle
                className={cn(
                  "h-2.5 w-2.5 fill-current",
                  statusColor[agent.status] || "text-gray-400"
                )}
              />
              <span className="text-xs text-gray-500 capitalize">{agent.status}</span>
            </div>
            {agent.last_run && (
              <span className="text-xs text-gray-400">
                {formatRelativeTime(agent.last_run)}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
