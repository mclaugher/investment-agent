import { FileText } from "lucide-react";
import { cn, formatDate } from "@/lib/utils";

interface AgentReportCardProps {
  report: {
    id: string;
    title: string;
    report_type: string;
    recommendation: string;
    confidence: number;
    created_at: string;
  };
}

const recBadge: Record<string, string> = {
  strong_buy: "bg-green-100 text-green-700",
  buy: "bg-green-50 text-green-600",
  hold: "bg-yellow-100 text-yellow-700",
  sell: "bg-red-50 text-red-600",
  strong_sell: "bg-red-100 text-red-700",
};

export function AgentReportCard({ report }: AgentReportCardProps) {
  const badgeClass = recBadge[report.recommendation] || "bg-gray-100 text-gray-600";

  return (
    <div className="border border-gray-200 rounded-lg p-3 hover:border-blue-300 transition-colors cursor-pointer">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2 min-w-0">
          <FileText className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{report.title}</p>
            <p className="text-xs text-gray-500 capitalize">{report.report_type}</p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span
            className={cn(
              "text-xs font-medium px-2 py-0.5 rounded-full capitalize",
              badgeClass
            )}
          >
            {report.recommendation.replace("_", " ")}
          </span>
          <span className="text-xs text-gray-500">
            {(report.confidence * 100).toFixed(0)}% conf
          </span>
        </div>
      </div>

      <div className="mt-2 text-xs text-gray-400">{formatDate(report.created_at)}</div>
    </div>
  );
}
