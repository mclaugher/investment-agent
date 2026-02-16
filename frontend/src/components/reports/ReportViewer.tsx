import ReactMarkdown from "react-markdown";
import { FileText, User, Tag, BarChart3 } from "lucide-react";
import { cn, formatDate } from "@/lib/utils";
import type { ReportDetail } from "@/types";

interface ReportViewerProps {
  report: ReportDetail;
}

const recBadge: Record<string, string> = {
  strong_buy: "bg-green-100 text-green-700",
  buy: "bg-green-50 text-green-600",
  hold: "bg-yellow-100 text-yellow-700",
  sell: "bg-red-50 text-red-600",
  strong_sell: "bg-red-100 text-red-700",
};

export function ReportViewer({ report }: ReportViewerProps) {
  const badgeClass = recBadge[report.recommendation] || "bg-gray-100 text-gray-600";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">{report.title}</h2>
        <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <User className="h-4 w-4" />
            <span>{report.agent_name}</span>
          </div>
          <div className="flex items-center gap-1">
            <FileText className="h-4 w-4" />
            <span className="capitalize">{report.report_type}</span>
          </div>
          {report.symbol && (
            <div className="flex items-center gap-1">
              <Tag className="h-4 w-4" />
              <span className="font-medium">{report.symbol}</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <BarChart3 className="h-4 w-4" />
            <span>{(report.confidence * 100).toFixed(0)}% confidence</span>
          </div>
          <span
            className={cn(
              "text-xs font-medium px-2.5 py-0.5 rounded-full capitalize",
              badgeClass
            )}
          >
            {report.recommendation.replace("_", " ")}
          </span>
        </div>
        <div className="text-xs text-gray-400 mt-2">{formatDate(report.created_at)}</div>
      </div>

      <hr className="border-gray-200" />

      <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-a:text-blue-600">
        <ReactMarkdown>{report.content}</ReactMarkdown>
      </div>

      {report.key_metrics && Object.keys(report.key_metrics).length > 0 && (
        <>
          <hr className="border-gray-200" />
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
              Key Metrics
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(report.key_metrics).map(([key, value]) => (
                <div key={key} className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 capitalize">
                    {key.replace(/_/g, " ")}
                  </p>
                  <p className="text-sm font-semibold text-gray-900 mt-0.5">
                    {typeof value === "number" ? value.toLocaleString() : String(value)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
