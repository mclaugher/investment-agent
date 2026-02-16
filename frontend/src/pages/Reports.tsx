import { useEffect, useState, useCallback } from "react";
import { usePortfolioStore } from "@/store/portfolioStore";
import { ReportList, type ReportFilters } from "@/components/reports/ReportList";
import { ReportViewer } from "@/components/reports/ReportViewer";
import type { ReportSummary, ReportDetail } from "@/types";

// Placeholder: in production these would come from an API store
const PLACEHOLDER_REPORTS: ReportSummary[] = [];

export default function Reports() {
  const [reports, setReports] = useState<ReportSummary[]>(PLACEHOLDER_REPORTS);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<ReportDetail | null>(null);
  const limit = 20;

  const handleFilterChange = useCallback((filters: ReportFilters) => {
    // Placeholder: would call API with filters
    setPage(1);
  }, []);

  const handleSelect = useCallback((id: string) => {
    setSelectedId(id);
    // Placeholder: would fetch full report detail from API
    setSelectedReport(null);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <p className="text-sm text-gray-500 mt-1">
          Analysis reports from all agents
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-220px)]">
        <div className="lg:col-span-1 overflow-hidden">
          <ReportList
            reports={reports}
            total={total}
            page={page}
            limit={limit}
            selectedId={selectedId}
            onSelect={handleSelect}
            onPageChange={setPage}
            onFilterChange={handleFilterChange}
          />
        </div>
        <div className="lg:col-span-2 overflow-y-auto">
          {selectedReport ? (
            <ReportViewer report={selectedReport} />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center h-full flex items-center justify-center">
              <p className="text-sm text-gray-500">
                {selectedId
                  ? "Loading report..."
                  : "Select a report to view its details."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
