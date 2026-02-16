import { useEffect } from "react";
import { usePortfolioStore } from "../store/portfolioStore";

/**
 * Hook that fetches portfolio summary and holdings on mount
 * and returns the current portfolio store state.
 */
export function usePortfolio() {
  const summary = usePortfolioStore((s) => s.summary);
  const holdings = usePortfolioStore((s) => s.holdings);
  const loading = usePortfolioStore((s) => s.loading);
  const error = usePortfolioStore((s) => s.error);
  const fetchSummary = usePortfolioStore((s) => s.fetchSummary);
  const fetchHoldings = usePortfolioStore((s) => s.fetchHoldings);

  useEffect(() => {
    fetchSummary();
    fetchHoldings();
  }, [fetchSummary, fetchHoldings]);

  return { summary, holdings, loading, error };
}
