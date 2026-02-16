import { Activity } from "lucide-react";
import { cn, formatCurrency, formatPercent, formatRelativeTime } from "@/lib/utils";
import { usePortfolioStore } from "@/store/portfolioStore";

export function Header() {
  const summary = usePortfolioStore((s) => s.summary);
  const lastAnalysis = usePortfolioStore((s) => s.lastAnalysisAt);

  return (
    <header className="sticky top-0 z-20 h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <h1 className="text-lg font-semibold text-gray-900">
        Superhuman Alpha Fund
      </h1>

      <div className="flex items-center gap-6 text-sm">
        {summary && (
          <>
            <div className="flex items-center gap-2">
              <span className="text-gray-500">Portfolio Value</span>
              <span className="font-semibold text-gray-900">
                {formatCurrency(summary.total_value)}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-gray-500">Daily P&L</span>
              <span
                className={cn(
                  "font-semibold",
                  summary.daily_pnl >= 0 ? "text-green-600" : "text-red-600"
                )}
              >
                {formatCurrency(summary.daily_pnl)} ({formatPercent(summary.daily_pnl_pct)})
              </span>
            </div>
          </>
        )}

        {lastAnalysis && (
          <div className="flex items-center gap-1.5 text-gray-500">
            <Activity className="h-4 w-4" />
            <span>Last analysis: {formatRelativeTime(lastAnalysis)}</span>
          </div>
        )}
      </div>
    </header>
  );
}
