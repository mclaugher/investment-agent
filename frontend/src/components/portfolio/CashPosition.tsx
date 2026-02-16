import { Wallet } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

interface CashPositionProps {
  cashBalance: number;
  minReserve: number;
  totalValue: number;
}

export function CashPosition({ cashBalance, minReserve, totalValue }: CashPositionProps) {
  const reserveAmount = totalValue * (minReserve / 100);
  const available = Math.max(0, cashBalance - reserveAmount);
  const reservePct = totalValue > 0 ? (reserveAmount / cashBalance) * 100 : 0;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Wallet className="h-5 w-5 text-gray-400" />
        <h3 className="text-sm font-semibold text-gray-900">Cash Position</h3>
      </div>

      <div className="space-y-4">
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Cash Balance</span>
          <span className="text-sm font-semibold text-gray-900">
            {formatCurrency(cashBalance)}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-sm text-gray-500">
            Min Reserve ({minReserve}%)
          </span>
          <span className="text-sm font-medium text-gray-700">
            {formatCurrency(reserveAmount)}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Available for Investment</span>
          <span className="text-sm font-semibold text-green-600">
            {formatCurrency(available)}
          </span>
        </div>

        <div className="pt-2">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Reserve</span>
            <span>Available</span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-yellow-400 rounded-full"
              style={{ width: `${Math.min(100, reservePct)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
