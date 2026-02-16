import { create } from "zustand";
import type { PortfolioSummary, Holding, Transaction } from "../types";
import {
  fetchPortfolio as apiFetchPortfolio,
  fetchHoldings as apiFetchHoldings,
  fetchTransactions as apiFetchTransactions,
} from "../lib/api";

interface PortfolioState {
  summary: PortfolioSummary | null;
  holdings: Holding[];
  transactions: Transaction[];
  transactionsTotal: number;
  loading: boolean;
  error: string | null;
  fetchSummary: () => Promise<void>;
  fetchHoldings: () => Promise<void>;
  fetchTransactions: (page: number, limit: number) => Promise<void>;
  updatePrice: (symbol: string, price: number) => void;
}

export const usePortfolioStore = create<PortfolioState>()((set, get) => ({
  summary: null,
  holdings: [],
  transactions: [],
  transactionsTotal: 0,
  loading: false,
  error: null,

  fetchSummary: async () => {
    set({ loading: true, error: null });
    try {
      const summary = await apiFetchPortfolio();
      set({ summary, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to fetch portfolio",
        loading: false,
      });
    }
  },

  fetchHoldings: async () => {
    set({ loading: true, error: null });
    try {
      const holdings = await apiFetchHoldings();
      set({ holdings, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to fetch holdings",
        loading: false,
      });
    }
  },

  fetchTransactions: async (page: number, limit: number) => {
    try {
      const data = await apiFetchTransactions(page, limit);
      set({ transactions: data.items, transactionsTotal: data.total });
    } catch {
      // silently fail
    }
  },

  updatePrice: (symbol: string, price: number) => {
    const { holdings } = get();
    const updated = holdings.map((h) => {
      if (h.symbol !== symbol) return h;
      const market_value = h.shares * price;
      const unrealized_pnl = (price - h.avg_cost_basis) * h.shares;
      const unrealized_pnl_pct =
        h.avg_cost_basis > 0
          ? ((price - h.avg_cost_basis) / h.avg_cost_basis) * 100
          : 0;
      return {
        ...h,
        current_price: price,
        market_value,
        unrealized_pnl,
        unrealized_pnl_pct,
      };
    });
    set({ holdings: updated });
  },
}));
