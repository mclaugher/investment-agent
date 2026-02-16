import { useSettingsStore } from "@/store/settingsStore";

export function PositionLimits() {
  const riskProfile = useSettingsStore((s) => s.riskProfile);
  const updateRiskProfile = useSettingsStore((s) => s.updateRiskProfile);

  const maxPosition = riskProfile?.max_single_position_pct ?? 5;
  const maxSector = riskProfile?.max_sector_pct ?? 25;
  const minCash = riskProfile?.min_cash_pct ?? 5;

  const handleChange = (field: string, value: number) => {
    updateRiskProfile({ [field]: value });
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900">Position Limits</h3>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Max Single Position %
          </label>
          <input
            type="number"
            min={1}
            max={100}
            step={0.5}
            value={maxPosition}
            onChange={(e) =>
              handleChange("max_single_position_pct", Number(e.target.value))
            }
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">
            No single holding can exceed this %.
          </p>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Max Sector %</label>
          <input
            type="number"
            min={1}
            max={100}
            step={0.5}
            value={maxSector}
            onChange={(e) =>
              handleChange("max_sector_pct", Number(e.target.value))
            }
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">
            No sector allocation can exceed this %.
          </p>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Min Cash Reserve %</label>
          <input
            type="number"
            min={0}
            max={100}
            step={0.5}
            value={minCash}
            onChange={(e) =>
              handleChange("min_cash_pct", Number(e.target.value))
            }
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-400 mt-1">
            Minimum cash that must be held at all times.
          </p>
        </div>
      </div>
    </div>
  );
}
