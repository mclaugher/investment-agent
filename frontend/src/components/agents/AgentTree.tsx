import { cn } from "@/lib/utils";
import { Circle } from "lucide-react";
import type { AgentSummary } from "@/types";

interface AgentNode {
  name: string;
  role: string;
  children?: AgentNode[];
}

const AGENT_HIERARCHY: AgentNode = {
  name: "CEO Agent",
  role: "ceo",
  children: [
    {
      name: "CIO Agent",
      role: "cio",
      children: [
        {
          name: "Tech Supervisor",
          role: "supervisor",
          children: [
            { name: "Tech Fundamental Analyst", role: "analyst" },
            { name: "Tech Technical Analyst", role: "analyst" },
            { name: "Tech Sentiment Analyst", role: "analyst" },
          ],
        },
        {
          name: "Healthcare Supervisor",
          role: "supervisor",
          children: [
            { name: "HC Fundamental Analyst", role: "analyst" },
            { name: "HC Technical Analyst", role: "analyst" },
            { name: "HC Sentiment Analyst", role: "analyst" },
          ],
        },
        {
          name: "Finance Supervisor",
          role: "supervisor",
          children: [
            { name: "Fin Fundamental Analyst", role: "analyst" },
            { name: "Fin Technical Analyst", role: "analyst" },
            { name: "Fin Sentiment Analyst", role: "analyst" },
          ],
        },
      ],
    },
    { name: "Risk Manager", role: "risk_manager" },
    { name: "Macro Strategist", role: "macro" },
  ],
};

interface AgentTreeProps {
  agents: AgentSummary[];
  selectedAgent: string | null;
  onSelect: (name: string) => void;
}

function TreeNode({
  node,
  agents,
  selectedAgent,
  onSelect,
  depth = 0,
}: {
  node: AgentNode;
  agents: AgentSummary[];
  selectedAgent: string | null;
  onSelect: (name: string) => void;
  depth?: number;
}) {
  const agentData = agents.find((a) => a.name === node.name);
  const isSelected = selectedAgent === node.name;

  const statusColor =
    agentData?.status === "idle"
      ? "text-green-500"
      : agentData?.status === "running"
      ? "text-yellow-500"
      : "text-gray-400";

  return (
    <div className={cn("relative", depth > 0 && "ml-6")}>
      {depth > 0 && (
        <div className="absolute left-[-16px] top-0 bottom-0 w-px bg-gray-200" />
      )}
      {depth > 0 && (
        <div className="absolute left-[-16px] top-4 w-4 h-px bg-gray-200" />
      )}

      <button
        onClick={() => onSelect(node.name)}
        className={cn(
          "w-full text-left px-3 py-2 rounded-lg border transition-colors mb-1",
          isSelected
            ? "border-blue-500 bg-blue-50"
            : "border-gray-200 bg-white hover:border-blue-300"
        )}
      >
        <div className="flex items-center gap-2">
          <Circle className={cn("h-2.5 w-2.5 fill-current flex-shrink-0", statusColor)} />
          <span className="text-sm font-medium text-gray-900 truncate">{node.name}</span>
        </div>
        <span className="text-xs text-gray-500 capitalize ml-[18px]">{node.role}</span>
      </button>

      {node.children && (
        <div className="relative">
          {node.children.map((child) => (
            <TreeNode
              key={child.name}
              node={child}
              agents={agents}
              selectedAgent={selectedAgent}
              onSelect={onSelect}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function AgentTree({ agents, selectedAgent, onSelect }: AgentTreeProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 overflow-y-auto">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Agent Hierarchy</h3>
      <TreeNode
        node={AGENT_HIERARCHY}
        agents={agents}
        selectedAgent={selectedAgent}
        onSelect={onSelect}
      />
    </div>
  );
}
