import { useState, useEffect } from "react";
import { Save } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSettingsStore } from "@/store/settingsStore";

export function RiskProfileEditor() {
  const riskProfile = useSettingsStore((s) => s.riskProfile);
  const updateRiskProfile = useSettingsStore((s) => s.updateRiskProfile);

  const [aggressiveness, setAggressiveness] = useState(5);
  const [equityPct, setEquityPct] = useState(60);
  const [fixedIncomePct, setFixedIncomePct] = useState(30);
  const [cashPct, setCashPct] = useState(10);

  useEffect(() => {
    if (riskProfile) {
      setAggressiveness(Number(riskProfile.aggressiveness) || 5);
      setEquityPct(riskProfile.target_equity_pct);
      setFixedIncomePct(riskProfile.target_fixed_income_pct);
      setCashPct(riskProfile.target_cash_pct);
    }
  }, [riskProfile]);

  const total = equityPct + fixedIncomePct + cashPct;
  const isValid = Math.abs(total - 100) < 0.01;

  const aggressivenessLabel =
    aggressiveness <= 3
      ? "Conservative"
      : aggressiveness <= 6
      ? "Moderate"
      : "Aggressive";

  const handleSave = () => {
    if (!isValid) return;
    updateRiskProfile({
      aggressiveness: String(aggressiveness),
      target_equity_pct: equityPct,
      target_fixed_income_pct: fixedIncomePct,
      target_cash_pct: cashPct,
    });
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-5">
      <h3 className="text-sm font-semibold text-gray-900">Risk Profile</h3>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm text-gray-700">Aggressiveness</label>
          <span className="text-sm font-medium text-gray-900">
            {aggressiveness} - {aggressivenessLabel}
          </span>
        </div>
        <input
          type="range"
          min={1}
          max={10}
          value={aggressiveness}
          onChange={(e) => setAggressiveness(Number(e.target.value))}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-400">
          <span>Conservative</span>
          <span>Aggressive</span>
        </div>
      </div>

      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-700">
          Allocation Targets{" "}
          <span className={cn("text-xs", isValid ? "text-green-600" : "text-red-600")}>
            (Total: {total.toFixed(1)}%)
          </span>
        </h4>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Equity %</label>
            <input
              type="number"
              min={0}
              max={100}
              value={equityPct}
              onChange={(e) => setEquityPct(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Fixed Income %</label>
            <input
              type="number"
              min={0}
              max={100}
              value={fixedIncomePct}
              onChange={(e) => setFixedIncomePct(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Cash %</label>
            <input
              type="number"
              min={0}
              max={100}
              value={cashPct}
              onChange={(e) => setCashPct(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={!isValid}
        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg disabled:opacity-50 hover:bg-blue-700 transition-colors"
      >
        <Save className="h-4 w-4" />
        Save Profile
      </button>
    </div>
  );
}
