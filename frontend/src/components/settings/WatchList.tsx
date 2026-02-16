import { useState } from "react";
import { X, Plus } from "lucide-react";
import { useSettingsStore } from "@/store/settingsStore";

export function WatchList() {
  const watchlist = useSettingsStore((s) => s.watchlist);
  const addSymbol = useSettingsStore((s) => s.addWatchlistSymbol);
  const removeSymbol = useSettingsStore((s) => s.removeWatchlistSymbol);

  const [input, setInput] = useState("");

  const handleAdd = () => {
    const symbol = input.trim().toUpperCase();
    if (!symbol) return;
    if (watchlist.includes(symbol)) {
      setInput("");
      return;
    }
    addSymbol(symbol);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900">Watch List</h3>

      <div className="flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value.toUpperCase())}
          onKeyDown={handleKeyDown}
          placeholder="Add symbol (e.g. AAPL)"
          className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleAdd}
          disabled={!input.trim()}
          className="inline-flex items-center gap-1 px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg disabled:opacity-50 hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {watchlist.map((symbol) => (
          <span
            key={symbol}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-700"
          >
            {symbol}
            <button
              onClick={() => removeSymbol(symbol)}
              className="text-gray-400 hover:text-red-500 transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </span>
        ))}
        {watchlist.length === 0 && (
          <p className="text-sm text-gray-500">No symbols in watch list.</p>
        )}
      </div>
    </div>
  );
}
