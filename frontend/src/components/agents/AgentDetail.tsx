import { Bot, Circle, Wrench, Clock } from "lucide-react";
import { cn, formatDate, formatRelativeTime } from "@/lib/utils";
import { AgentReportCard } from "./AgentReportCard";
import type { AgentDetail as AgentDetailType } from "@/types";

interface AgentDetailProps {
  agent: AgentDetailType;
}

export function AgentDetail({ agent }: AgentDetailProps) {
  const statusColor =
    agent.status === "idle"
      ? "text-green-500"
      : agent.status === "running"
      ? "text-yellow-500"
      : "text-red-500";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-5">
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
          <Bot className="h-5 w-5 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold text-gray-900">{agent.name}</h2>
          <p className="text-sm text-gray-500 capitalize">{agent.role}</p>
        </div>
        <div className="flex items-center gap-1.5">
          <Circle className={cn("h-2.5 w-2.5 fill-current", statusColor)} />
          <span className="text-sm text-gray-600 capitalize">{agent.status}</span>
        </div>
      </div>

      <p className="text-sm text-gray-700">{agent.description}</p>

      <div className="space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          Tools
        </h4>
        <div className="flex flex-wrap gap-2">
          {agent.tools.map((tool) => (
            <span
              key={tool}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-gray-100 text-xs text-gray-700"
            >
              <Wrench className="h-3 w-3" />
              {tool}
            </span>
          ))}
          {agent.tools.length === 0 && (
            <span className="text-xs text-gray-500">No tools assigned.</span>
          )}
        </div>
      </div>

      <div className="flex gap-6 text-sm">
        {agent.last_run && (
          <div className="flex items-center gap-1.5 text-gray-500">
            <Clock className="h-4 w-4" />
            <span>Last run: {formatRelativeTime(agent.last_run)}</span>
          </div>
        )}
        <div className="text-gray-500">
          {agent.reports_count} report{agent.reports_count !== 1 ? "s" : ""}
        </div>
      </div>

      {agent.recent_reports.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Recent Reports
          </h4>
          <div className="space-y-2">
            {agent.recent_reports.map((report) => (
              <AgentReportCard key={report.id} report={report} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
