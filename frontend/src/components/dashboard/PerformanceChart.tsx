import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { cn } from "@/lib/utils";

const TIME_PERIODS = ["1M", "3M", "6M", "1Y", "ALL"] as const;
type TimePeriod = (typeof TIME_PERIODS)[number];

// Placeholder data -- will be replaced with real performance series
function generatePlaceholderData(period: TimePeriod) {
  const points =
    period === "1M" ? 30 : period === "3M" ? 90 : period === "6M" ? 180 : period === "1Y" ? 365 : 730;
  const data = [];
  let portfolioValue = 1000000;
  let benchmarkValue = 1000000;

  for (let i = 0; i < points; i += Math.max(1, Math.floor(points / 60))) {
    portfolioValue += (Math.random() - 0.48) * 5000;
    benchmarkValue += (Math.random() - 0.48) * 4000;
    const date = new Date();
    date.setDate(date.getDate() - (points - i));
    data.push({
      date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      portfolio: Math.round(portfolioValue),
      benchmark: Math.round(benchmarkValue),
    });
  }
  return data;
}

export function PerformanceChart() {
  const [period, setPeriod] = useState<TimePeriod>("3M");
  const data = generatePlaceholderData(period);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Performance</h3>
        <div className="flex gap-1">
          {TIME_PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={cn(
                "px-3 py-1 rounded-md text-xs font-medium transition-colors",
                period === p
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" />
            <YAxis
              tick={{ fontSize: 11 }}
              stroke="#94a3b8"
              tickFormatter={(v: number) =>
                `$${(v / 1000).toFixed(0)}k`
              }
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                fontSize: "12px",
              }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, undefined]}
            />
            <Line
              type="monotone"
              dataKey="portfolio"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={false}
              name="Portfolio"
            />
            <Line
              type="monotone"
              dataKey="benchmark"
              stroke="#94A3B8"
              strokeWidth={2}
              dot={false}
              name="Benchmark"
              strokeDasharray="4 4"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <div className="h-0.5 w-4 bg-blue-600 rounded" />
          Portfolio
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-0.5 w-4 bg-gray-400 rounded border-dashed" />
          Benchmark (S&P 500)
        </div>
      </div>
    </div>
  );
}
