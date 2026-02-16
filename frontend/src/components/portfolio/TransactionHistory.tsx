import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
import type { Transaction } from "@/types";

interface TransactionHistoryProps {
  transactions: Transaction[];
  total: number;
  page: number;
  limit: number;
  onPageChange: (page: number) => void;
}

export function TransactionHistory({
  transactions,
  total,
  page,
  limit,
  onPageChange,
}: TransactionHistoryProps) {
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900">Transaction History</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-4 py-3 text-left font-medium text-gray-500">Date</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Symbol</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Action</th>
              <th className="px-4 py-3 text-right font-medium text-gray-500">Shares</th>
              <th className="px-4 py-3 text-right font-medium text-gray-500">Price</th>
              <th className="px-4 py-3 text-right font-medium text-gray-500">Total</th>
              <th className="px-4 py-3 text-left font-medium text-gray-500">Decision</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr
                key={tx.id}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 text-gray-600">{formatDate(tx.executed_at)}</td>
                <td className="px-4 py-3 font-semibold text-gray-900">{tx.symbol}</td>
                <td className="px-4 py-3">
                  <span
                    className={cn(
                      "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
                      tx.action === "BUY"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    )}
                  >
                    {tx.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-gray-700">
                  {tx.shares.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right text-gray-700">
                  {formatCurrency(tx.price_per_share)}
                </td>
                <td className="px-4 py-3 text-right font-medium text-gray-900">
                  {formatCurrency(tx.total_amount)}
                </td>
                <td className="px-4 py-3">
                  <a
                    href={`/reports?decision=${tx.agent_decision_id}`}
                    className="text-blue-600 hover:underline text-xs"
                  >
                    View
                  </a>
                </td>
              </tr>
            ))}
            {transactions.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No transactions found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-200">
          <span className="text-sm text-gray-500">
            Page {page} of {totalPages} ({total} total)
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-1.5 rounded-md border border-gray-200 disabled:opacity-50 hover:bg-gray-100 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-1.5 rounded-md border border-gray-200 disabled:opacity-50 hover:bg-gray-100 transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
