import { useEffect } from "react";
import { usePortfolioStore } from "@/store/portfolioStore";
import { PortfolioSummary } from "@/components/dashboard/PortfolioSummary";
import { AllocationChart } from "@/components/dashboard/AllocationChart";
import { PerformanceChart } from "@/components/dashboard/PerformanceChart";
import { RecentDecisions } from "@/components/dashboard/RecentDecisions";
import { AgentStatusGrid } from "@/components/dashboard/AgentStatusGrid";

export default function Dashboard() {
  const summary = usePortfolioStore((s) => s.summary);
  const fetchSummary = usePortfolioStore((s) => s.fetchSummary);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Portfolio overview and agent activity
        </p>
      </div>

      <PortfolioSummary />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AllocationChart allocation={summary?.allocation ?? {}} />
        <PerformanceChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentDecisions />
        <AgentStatusGrid />
      </div>
    </div>
  );
}
