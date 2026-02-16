import { ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";
import { cn, formatDate } from "@/lib/utils";

interface Decision {
  id: string;
  symbol: string;
  action: "BUY" | "SELL" | "HOLD";
  status: "approved" | "human_review" | "rejected";
  confidence: number;
  timestamp: string;
}

// Placeholder sample decisions
const SAMPLE_DECISIONS: Decision[] = [
  { id: "1", symbol: "AAPL", action: "BUY", status: "approved", confidence: 0.87, timestamp: "2026-02-15T10:30:00Z" },
  { id: "2", symbol: "MSFT", action: "HOLD", status: "approved", confidence: 0.72, timestamp: "2026-02-15T10:28:00Z" },
  { id: "3", symbol: "TSLA", action: "SELL", status: "human_review", confidence: 0.65, timestamp: "2026-02-15T09:45:00Z" },
  { id: "4", symbol: "NVDA", action: "BUY", status: "approved", confidence: 0.91, timestamp: "2026-02-14T16:00:00Z" },
  { id: "5", symbol: "JPM", action: "BUY", status: "rejected", confidence: 0.52, timestamp: "2026-02-14T15:30:00Z" },
];

const statusStyles: Record<Decision["status"], string> = {
  approved: "bg-green-100 text-green-700",
  human_review: "bg-yellow-100 text-yellow-700",
  rejected: "bg-red-100 text-red-700",
};

const statusLabels: Record<Decision["status"], string> = {
  approved: "Approved",
  human_review: "Review",
  rejected: "Rejected",
};

export function RecentDecisions() {
  const decisions = SAMPLE_DECISIONS;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Recent Decisions</h3>

      <div className="space-y-3">
        {decisions.map((d) => (
          <div
            key={d.id}
            className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
          >
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "h-8 w-8 rounded-lg flex items-center justify-center",
                  d.action === "BUY"
                    ? "bg-green-100"
                    : d.action === "SELL"
                    ? "bg-red-100"
                    : "bg-gray-100"
                )}
              >
                {d.action === "BUY" ? (
                  <ArrowUpRight className="h-4 w-4 text-green-600" />
                ) : d.action === "SELL" ? (
                  <ArrowDownRight className="h-4 w-4 text-red-600" />
                ) : (
                  <Clock className="h-4 w-4 text-gray-500" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-900">{d.symbol}</span>
                  <span
                    className={cn(
                      "text-xs font-medium",
                      d.action === "BUY"
                        ? "text-green-600"
                        : d.action === "SELL"
                        ? "text-red-600"
                        : "text-gray-500"
                    )}
                  >
                    {d.action}
                  </span>
                </div>
                <span className="text-xs text-gray-500">{formatDate(d.timestamp)}</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-500">
                {(d.confidence * 100).toFixed(0)}% conf
              </span>
              <span
                className={cn(
                  "text-xs font-medium px-2 py-0.5 rounded-full",
                  statusStyles[d.status]
                )}
              >
                {statusLabels[d.status]}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
