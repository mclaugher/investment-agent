import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { formatCurrency, formatPercent } from "@/lib/utils";

const COLORS = [
  "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
  "#EC4899", "#06B6D4", "#F97316", "#6366F1", "#14B8A6",
  "#A3E635", "#64748B",
];

interface AllocationChartProps {
  allocation: Record<string, number>;
}

interface ChartEntry {
  name: string;
  value: number;
}

function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0].payload as ChartEntry;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-sm">
      <p className="font-medium text-gray-900">{name}</p>
      <p className="text-gray-600">{formatCurrency(value)}</p>
    </div>
  );
}

export function AllocationChart({ allocation }: AllocationChartProps) {
  const data: ChartEntry[] = Object.entries(allocation).map(([name, value]) => ({
    name,
    value,
  }));

  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Sector Allocation</h3>
        <p className="text-sm text-gray-500">No allocation data available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Sector Allocation</h3>
      <div className="flex items-center gap-6">
        <div className="w-48 h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="value"
                strokeWidth={2}
                stroke="#fff"
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="flex-1 space-y-2">
          {data.map((entry, index) => (
            <div key={entry.name} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-gray-700">{entry.name}</span>
              </div>
              <span className="font-medium text-gray-900">
                {total > 0 ? ((entry.value / total) * 100).toFixed(1) : 0}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
