import { useState } from "react";
import { Play, Clock } from "lucide-react";
import type { ScheduleEntry } from "@/types";

const SCHEDULES: ScheduleEntry[] = [
  {
    name: "Daily Analysis Cycle",
    task: "daily-analysis-cycle",
    schedule: "Weekdays 6:00 AM ET",
    description: "Full multi-agent analysis of all watched securities and portfolio review.",
  },
  {
    name: "Price Data Refresh",
    task: "price-refresh",
    schedule: "Every 15 minutes (market hours)",
    description: "Fetch latest prices and update portfolio valuations.",
  },
  {
    name: "News & Sentiment Scan",
    task: "news-scan",
    schedule: "Every 2 hours",
    description: "Scan news sources and social media for sentiment signals.",
  },
  {
    name: "Risk Check",
    task: "risk-check",
    schedule: "Hourly (market hours)",
    description: "Verify all positions against risk limits and flag violations.",
  },
];

export function ScheduleConfig() {
  const [running, setRunning] = useState<string | null>(null);

  const handleRunNow = async (task: string) => {
    setRunning(task);
    // Placeholder: will call API to trigger task
    setTimeout(() => setRunning(null), 3000);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Clock className="h-5 w-5 text-gray-400" />
        <h3 className="text-sm font-semibold text-gray-900">Scheduled Tasks</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 px-3 font-medium text-gray-500">Task</th>
              <th className="text-left py-2 px-3 font-medium text-gray-500">Schedule</th>
              <th className="text-left py-2 px-3 font-medium text-gray-500">Description</th>
              <th className="text-right py-2 px-3 font-medium text-gray-500">Action</th>
            </tr>
          </thead>
          <tbody>
            {SCHEDULES.map((s) => (
              <tr key={s.task} className="border-b border-gray-100">
                <td className="py-3 px-3 font-medium text-gray-900">{s.name}</td>
                <td className="py-3 px-3 text-gray-600">{s.schedule}</td>
                <td className="py-3 px-3 text-gray-600">{s.description}</td>
                <td className="py-3 px-3 text-right">
                  {s.task === "daily-analysis-cycle" && (
                    <button
                      onClick={() => handleRunNow(s.task)}
                      disabled={running === s.task}
                      className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                      <Play className="h-3 w-3" />
                      {running === s.task ? "Running..." : "Run Now"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
