import { useState } from "react";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import type { ReportSummary } from "@/types";

interface ReportListProps {
  reports: ReportSummary[];
  total: number;
  page: number;
  limit: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onPageChange: (page: number) => void;
  onFilterChange: (filters: ReportFilters) => void;
}

export interface ReportFilters {
  agent: string;
  sector: string;
  symbol: string;
  reportType: string;
  search: string;
}

const recBadge: Record<string, string> = {
  strong_buy: "bg-green-100 text-green-700",
  buy: "bg-green-50 text-green-600",
  hold: "bg-yellow-100 text-yellow-700",
  sell: "bg-red-50 text-red-600",
  strong_sell: "bg-red-100 text-red-700",
};

export function ReportList({
  reports,
  total,
  page,
  limit,
  selectedId,
  onSelect,
  onPageChange,
  onFilterChange,
}: ReportListProps) {
  const [filters, setFilters] = useState<ReportFilters>({
    agent: "",
    sector: "",
    symbol: "",
    reportType: "",
    search: "",
  });

  const totalPages = Math.ceil(total / limit);

  const updateFilter = (key: keyof ReportFilters, value: string) => {
    const next = { ...filters, [key]: value };
    setFilters(next);
    onFilterChange(next);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 flex flex-col h-full">
      <div className="px-4 py-3 border-b border-gray-200 space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Reports</h3>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search reports..."
            value={filters.search}
            onChange={(e) => updateFilter("search", e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <select
            value={filters.agent}
            onChange={(e) => updateFilter("agent", e.target.value)}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Agents</option>
            <option value="CEO Agent">CEO Agent</option>
            <option value="CIO Agent">CIO Agent</option>
            <option value="Risk Manager">Risk Manager</option>
          </select>
          <select
            value={filters.sector}
            onChange={(e) => updateFilter("sector", e.target.value)}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Sectors</option>
            <option value="Technology">Technology</option>
            <option value="Healthcare">Healthcare</option>
            <option value="Financial">Financial</option>
          </select>
          <select
            value={filters.reportType}
            onChange={(e) => updateFilter("reportType", e.target.value)}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            <option value="fundamental">Fundamental</option>
            <option value="technical">Technical</option>
            <option value="sentiment">Sentiment</option>
            <option value="sector_summary">Sector Summary</option>
            <option value="portfolio_review">Portfolio Review</option>
          </select>
          <input
            type="text"
            placeholder="Symbol..."
            value={filters.symbol}
            onChange={(e) => updateFilter("symbol", e.target.value.toUpperCase())}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
        {reports.map((r) => (
          <button
            key={r.id}
            onClick={() => onSelect(r.id)}
            className={cn(
              "w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors",
              selectedId === r.id && "bg-blue-50 border-l-2 border-blue-500"
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-gray-900 truncate">{r.title}</p>
              <span
                className={cn(
                  "text-xs font-medium px-2 py-0.5 rounded-full capitalize flex-shrink-0",
                  recBadge[r.recommendation] || "bg-gray-100 text-gray-600"
                )}
              >
                {r.recommendation.replace("_", " ")}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
              <span>{r.agent_name}</span>
              <span>-</span>
              <span className="capitalize">{r.report_type}</span>
              {r.symbol && (
                <>
                  <span>-</span>
                  <span className="font-medium">{r.symbol}</span>
                </>
              )}
            </div>
            <div className="text-xs text-gray-400 mt-1">{formatDate(r.created_at)}</div>
          </button>
        ))}
        {reports.length === 0 && (
          <div className="px-4 py-8 text-center text-sm text-gray-500">
            No reports found.
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
          <span className="text-xs text-gray-500">
            {page}/{totalPages}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-1 rounded border border-gray-200 disabled:opacity-50 hover:bg-gray-100"
            >
              <ChevronLeft className="h-3 w-3" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-1 rounded border border-gray-200 disabled:opacity-50 hover:bg-gray-100"
            >
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
