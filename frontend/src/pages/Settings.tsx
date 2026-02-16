import { useEffect } from "react";
import { useSettingsStore } from "@/store/settingsStore";
import { RiskProfileEditor } from "@/components/settings/RiskProfileEditor";
import { PositionLimits } from "@/components/settings/PositionLimits";
import { WatchList } from "@/components/settings/WatchList";
import { ScheduleConfig } from "@/components/settings/ScheduleConfig";

export default function Settings() {
  const fetchSettings = useSettingsStore((s) => s.fetchSettings);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">
          Risk profile, position limits, watch list, and scheduling
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskProfileEditor />
        <PositionLimits />
      </div>

      <WatchList />
      <ScheduleConfig />
    </div>
  );
}
