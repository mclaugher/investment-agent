import { TrendingUp, TrendingDown, DollarSign, Wallet, BarChart3, PiggyBank } from "lucide-react";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { usePortfolioStore } from "@/store/portfolioStore";

interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  positive?: boolean;
  icon: React.ReactNode;
}

function MetricCard({ title, value, change, positive, icon }: MetricCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-500">{title}</span>
        <div className="h-9 w-9 rounded-lg bg-gray-100 flex items-center justify-center text-gray-600">
          {icon}
        </div>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {change !== undefined && (
        <div className="flex items-center gap-1">
          {positive !== undefined &&
            (positive ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            ))}
          <span
            className={cn(
              "text-sm font-medium",
              positive === undefined
                ? "text-gray-500"
                : positive
                ? "text-green-600"
                : "text-red-600"
            )}
          >
            {change}
          </span>
        </div>
      )}
    </div>
  );
}

export function PortfolioSummary() {
  const summary = usePortfolioStore((s) => s.summary);

  if (!summary) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="bg-white rounded-xl border border-gray-200 p-5 h-32 animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Total Value"
        value={formatCurrency(summary.total_value)}
        icon={<DollarSign className="h-5 w-5" />}
      />
      <MetricCard
        title="Daily P&L"
        value={formatCurrency(summary.daily_pnl)}
        change={formatPercent(summary.daily_pnl_pct)}
        positive={summary.daily_pnl >= 0}
        icon={<BarChart3 className="h-5 w-5" />}
      />
      <MetricCard
        title="Total Return"
        value={formatPercent(summary.total_return_pct)}
        change={formatCurrency(summary.total_return)}
        positive={summary.total_return >= 0}
        icon={<TrendingUp className="h-5 w-5" />}
      />
      <MetricCard
        title="Cash Available"
        value={formatCurrency(summary.cash_balance)}
        icon={<Wallet className="h-5 w-5" />}
      />
    </div>
  );
}
