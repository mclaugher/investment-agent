import { useState } from "react";
import { ChevronRight, ChevronDown, User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DecisionTrailNode } from "@/types";

interface DecisionTrailProps {
  trail: DecisionTrailNode[];
}

function TrailNode({ node, depth = 0 }: { node: DecisionTrailNode; depth?: number }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;

  const recBadge: Record<string, string> = {
    strong_buy: "bg-green-100 text-green-700",
    buy: "bg-green-50 text-green-600",
    hold: "bg-yellow-100 text-yellow-700",
    sell: "bg-red-50 text-red-600",
    strong_sell: "bg-red-100 text-red-700",
  };

  const badgeClass = recBadge[node.recommendation] || "bg-gray-100 text-gray-600";

  return (
    <div className={cn("relative", depth > 0 && "ml-5 border-l border-gray-200 pl-4")}>
      <button
        onClick={() => hasChildren && setExpanded(!expanded)}
        className="flex items-start gap-2 w-full text-left py-2 group"
      >
        {hasChildren ? (
          expanded ? (
            <ChevronDown className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
          )
        ) : (
          <div className="h-4 w-4 flex-shrink-0" />
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <User className="h-3.5 w-3.5 text-gray-400" />
            <span className="text-sm font-medium text-gray-900">{node.agent_name}</span>
            <span className="text-xs text-gray-500 capitalize">({node.agent_role})</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-600 truncate">{node.title}</span>
            <span
              className={cn(
                "text-xs font-medium px-2 py-0.5 rounded-full capitalize flex-shrink-0",
                badgeClass
              )}
            >
              {node.recommendation.replace("_", " ")}
            </span>
            <span className="text-xs text-gray-400">
              {(node.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </button>

      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <TrailNode key={child.report_id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export function DecisionTrail({ trail }: DecisionTrailProps) {
  if (trail.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Decision Trail</h3>
        <p className="text-sm text-gray-500">No decision trail available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Decision Trail</h3>
      <div>
        {trail.map((node) => (
          <TrailNode key={node.report_id} node={node} />
        ))}
      </div>
    </div>
  );
}
