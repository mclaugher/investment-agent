import { useEffect, useState, useCallback } from "react";
import { usePortfolioStore } from "@/store/portfolioStore";
import { HoldingsTable } from "@/components/portfolio/HoldingsTable";
import { TransactionHistory } from "@/components/portfolio/TransactionHistory";
import { CashPosition } from "@/components/portfolio/CashPosition";
import type { Transaction } from "@/types";

export default function Portfolio() {
  const summary = usePortfolioStore((s) => s.summary);
  const holdings = usePortfolioStore((s) => s.holdings);
  const fetchSummary = usePortfolioStore((s) => s.fetchSummary);
  const fetchHoldings = usePortfolioStore((s) => s.fetchHoldings);
  const fetchTransactions = usePortfolioStore((s) => s.fetchTransactions);
  const transactions = usePortfolioStore((s) => s.transactions);
  const transactionsTotal = usePortfolioStore((s) => s.transactionsTotal);

  const [txPage, setTxPage] = useState(1);
  const txLimit = 10;

  useEffect(() => {
    fetchSummary();
    fetchHoldings();
  }, [fetchSummary, fetchHoldings]);

  useEffect(() => {
    fetchTransactions(txPage, txLimit);
  }, [fetchTransactions, txPage]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Portfolio</h1>
        <p className="text-sm text-gray-500 mt-1">
          Holdings, transactions, and cash management
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <HoldingsTable holdings={holdings} />
        </div>
        <div>
          <CashPosition
            cashBalance={summary?.cash_balance ?? 0}
            minReserve={5}
            totalValue={summary?.total_value ?? 0}
          />
        </div>
      </div>

      <TransactionHistory
        transactions={transactions}
        total={transactionsTotal}
        page={txPage}
        limit={txLimit}
        onPageChange={setTxPage}
      />
    </div>
  );
}
