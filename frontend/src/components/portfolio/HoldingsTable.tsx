import { useState } from "react";
import { ArrowUpDown } from "lucide-react";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import type { Holding } from "@/types";

interface HoldingsTableProps {
  holdings: Holding[];
}

type SortKey = keyof Holding;
type SortDir = "asc" | "desc";

export function HoldingsTable({ holdings }: HoldingsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("market_value");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const sorted = [...holdings].sort((a, b) => {
    const aVal = a[sortKey];
    const bVal = b[sortKey];
    if (typeof aVal === "number" && typeof bVal === "number") {
      return sortDir === "asc" ? aVal - bVal : bVal - aVal;
    }
    return sortDir === "asc"
      ? String(aVal).localeCompare(String(bVal))
      : String(bVal).localeCompare(String(aVal));
  });

  const columns: { key: SortKey; label: string; align?: string }[] = [
    { key: "symbol", label: "Symbol" },
    { key: "shares", label: "Shares", align: "right" },
    { key: "avg_cost_basis", label: "Avg Cost", align: "right" },
    { key: "current_price", label: "Price", align: "right" },
    { key: "market_value", label: "Mkt Value", align: "right" },
    { key: "unrealized_pnl", label: "P&L ($)", align: "right" },
    { key: "unrealized_pnl_pct", label: "P&L (%)", align: "right" },
    { key: "weight_pct", label: "Weight %", align: "right" },
    { key: "sector", label: "Sector" },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900">Holdings</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "px-4 py-3 font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none",
                    col.align === "right" ? "text-right" : "text-left"
                  )}
                  onClick={() => handleSort(col.key)}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    <ArrowUpDown className="h-3 w-3" />
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((h) => (
              <tr
                key={h.symbol}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 font-semibold text-gray-900">{h.symbol}</td>
                <td className="px-4 py-3 text-right text-gray-700">{h.shares.toLocaleString()}</td>
                <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(h.avg_cost_basis)}</td>
                <td className="px-4 py-3 text-right text-gray-700">{formatCurrency(h.current_price)}</td>
                <td className="px-4 py-3 text-right font-medium text-gray-900">
                  {formatCurrency(h.market_value)}
                </td>
                <td
                  className={cn(
                    "px-4 py-3 text-right font-medium",
                    h.unrealized_pnl >= 0 ? "text-green-600" : "text-red-600"
                  )}
                >
                  {formatCurrency(h.unrealized_pnl)}
                </td>
                <td
                  className={cn(
                    "px-4 py-3 text-right font-medium",
                    h.unrealized_pnl_pct >= 0 ? "text-green-600" : "text-red-600"
                  )}
                >
                  {formatPercent(h.unrealized_pnl_pct)}
                </td>
                <td className="px-4 py-3 text-right text-gray-700">
                  {h.weight_pct.toFixed(1)}%
                </td>
                <td className="px-4 py-3 text-gray-600">{h.sector}</td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                  No holdings found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
