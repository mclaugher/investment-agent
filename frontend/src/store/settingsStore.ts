import { create } from "zustand";
import type { RiskProfile } from "../types";
import {
  fetchRiskProfile as apiFetchRiskProfile,
  updateRiskProfile as apiUpdateRiskProfile,
  fetchWatchlist as apiFetchWatchlist,
  addToWatchlist as apiAddToWatchlist,
  removeFromWatchlist as apiRemoveFromWatchlist,
} from "../lib/api";

interface SettingsState {
  riskProfile: RiskProfile | null;
  watchlist: string[];
  loading: boolean;
  fetchSettings: () => Promise<void>;
  fetchRiskProfile: () => Promise<void>;
  updateRiskProfile: (updates: Partial<RiskProfile>) => Promise<void>;
  fetchWatchlist: () => Promise<void>;
  addSymbol: (symbol: string) => Promise<void>;
  removeSymbol: (symbol: string) => Promise<void>;
  addWatchlistSymbol: (symbol: string) => Promise<void>;
  removeWatchlistSymbol: (symbol: string) => Promise<void>;
}

export const useSettingsStore = create<SettingsState>()((set, get) => ({
  riskProfile: null,
  watchlist: [],
  loading: false,

  fetchSettings: async () => {
    set({ loading: true });
    try {
      const [riskProfile, watchlist] = await Promise.all([
        apiFetchRiskProfile(),
        apiFetchWatchlist(),
      ]);
      set({ riskProfile, watchlist, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchRiskProfile: async () => {
    set({ loading: true });
    try {
      const riskProfile = await apiFetchRiskProfile();
      set({ riskProfile, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  updateRiskProfile: async (updates: Partial<RiskProfile>) => {
    set({ loading: true });
    try {
      const riskProfile = await apiUpdateRiskProfile(updates);
      set({ riskProfile, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  fetchWatchlist: async () => {
    set({ loading: true });
    try {
      const watchlist = await apiFetchWatchlist();
      set({ watchlist, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  addSymbol: async (symbol: string) => {
    try {
      await apiAddToWatchlist(symbol);
      set({ watchlist: [...get().watchlist, symbol.toUpperCase()] });
    } catch {
      // Silently fail; could add error state if needed
    }
  },

  removeSymbol: async (symbol: string) => {
    try {
      await apiRemoveFromWatchlist(symbol);
      set({
        watchlist: get().watchlist.filter(
          (s) => s.toUpperCase() !== symbol.toUpperCase()
        ),
      });
    } catch {
      // Silently fail
    }
  },

  // Aliases used by components
  addWatchlistSymbol: async (symbol: string) => get().addSymbol(symbol),
  removeWatchlistSymbol: async (symbol: string) => get().removeSymbol(symbol),
}));
